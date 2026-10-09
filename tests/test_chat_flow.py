import asyncio
import json
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from app.main import app
from app.services import llm, rag, safety, speech
from app.config import settings
from scripts.ingest_knowledge_base import chunk_markdown_file

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
async def test_emergency_bypasses_retrieval_and_provider(monkeypatch):
    def fail(*args):
        raise AssertionError('Emergency must bypass model and retrieval')
    monkeypatch.setattr(llm, 'retrieve_context_with_sources', fail)
    monkeypatch.setattr(llm, '_chat_anthropic', fail)
    for language in ('en','hi','bn','ta','te','mr','gu','kn','ml','pa','ur'):
        result = await llm.chat_completion('I have chest pain', language)
        assert result['is_emergency'] is True
        assert result['language'] == language
        assert all(result[k] is None for k in ('allopathic','ayurvedic','unani','homeopathic'))
        if language != 'en':
            assert result['conversational_reply'] != safety.emergency_response('en')['conversational_reply']


@pytest.mark.asyncio
async def test_slow_retrieval_does_not_block_event_loop(monkeypatch):
    import threading
    started = threading.Event()
    release = threading.Event()
    def slow_retrieval(query):
        started.set()
        assert release.wait(timeout=2), 'Retrieval blocked the event loop'
        return {'context':'reference','sources':[]}
    async def provider(*args):
        return {'conversational_reply':'More details?', 'is_emergency':False}
    monkeypatch.setattr(llm,'retrieve_context_with_sources',slow_retrieval)
    monkeypatch.setattr(llm,'_chat_anthropic',provider)
    monkeypatch.setattr(settings,'LLM_PROVIDER','anthropic')
    task = asyncio.create_task(llm.chat_completion('mild discomfort'))
    try:
        for _ in range(100):
            if started.is_set(): break
            await asyncio.sleep(.01)
        assert started.is_set()
        # This can only run before retrieval completes if retrieval is offloaded.
        assert not task.done()
    finally:
        release.set()
    await task


@pytest.mark.asyncio
async def test_async_provider_calls(monkeypatch):
    create = AsyncMock(return_value=SimpleNamespace(content=[SimpleNamespace(type='text',text=json.dumps(follow_up()))]))
    monkeypatch.setattr(llm,'_get_anthropic_client',lambda:SimpleNamespace(messages=SimpleNamespace(create=create)))
    assert (await llm._chat_anthropic('hello','hi','',[]))['conversational_reply']=='ok'
    create.assert_awaited_once()
    generate = AsyncMock(return_value=SimpleNamespace(text=json.dumps(follow_up())))
    monkeypatch.setattr(llm,'_get_gemini_client',lambda:SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate))))
    await llm._chat_gemini('hello','hi','',[])
    generate.assert_awaited_once()
    assert generate.call_args.kwargs['config']['response_mime_type']=='application/json'
    assert 'max_output_tokens' not in generate.call_args.kwargs['config']


@pytest.mark.asyncio
async def test_model_emergency_suppresses_remedies(monkeypatch):
    monkeypatch.setattr(llm,'retrieve_context_with_sources',lambda _: {'context':'','sources':[]})
    monkeypatch.setattr(settings,'LLM_PROVIDER','anthropic')
    monkeypatch.setattr(llm,'_chat_anthropic',AsyncMock(return_value={'is_emergency':True,'allopathic':{'summary':'unsafe delay'}}))
    result = await llm.chat_completion('concerning symptoms','ta')
    assert result['is_emergency'] and result['allopathic'] is None


@pytest.mark.asyncio
async def test_voice_respects_selected_language(monkeypatch):
    import app.main as routes
    monkeypatch.setattr(routes,'transcribe_audio',AsyncMock(return_value={'text':'a question','language':'en'}))
    complete = AsyncMock(return_value={'conversational_reply':'उत्तर','language':'hi'})
    monkeypatch.setattr(routes,'chat_completion',complete)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
        response = await client.post('/voice-chat',files={'file':('sample.webm',b'audio')},data={'language':'hi','history':'[]'})
        assert response.status_code==200
        assert response.json()['detected_language']=='en'
        assert response.json()['language']=='hi'
        assert complete.call_args.kwargs['language']=='hi'
        bad = await client.post('/chat',data={'message':'hello','history':'invalid'})
        assert bad.status_code==400


def test_kb_provenance_and_locale_coverage():
    files=list((ROOT/'knowledge_base').glob('*.md'))
    assert len(files)==14
    chunks=[c for path in files for c in chunk_markdown_file(str(path))]
    assert len(chunks)==27
    sourced=[c for c in chunks if c['source_url']]
    assert len(sourced)==11
    assert all(c['reviewed_on']=='2026-10-09' for c in sourced)
    js=(ROOT/'app/static/i18n.js').read_text()
    locales=json.loads(js[js.index('{'):js.rindex(';')])
    assert len(locales)==11
    assert all(set(row)==set(locales['en']) for row in locales.values())
    assert all(all(isinstance(value,str) and value for value in row.values()) for row in locales.values())


def test_retrieval_empty_and_small_index(monkeypatch):
    collection=SimpleNamespace(count=lambda:1,query=lambda **kwargs: {'documents':[['safe context']], 'metadatas':[[{'source_url':'https://www.nhs.uk/','reviewed_on':'2026-10-09'}]]})
    monkeypatch.setattr(rag,'_get_collection',lambda:collection)
    result=rag.retrieve_context_with_sources('question')
    assert result['sources'][0]['source_url']=='https://www.nhs.uk/'
    collection.count=lambda:0
    assert rag.retrieve_context_with_sources('question')=={'context':'','sources':[]}


@pytest.mark.asyncio
async def test_transcription_cleans_up_on_failure(monkeypatch,tmp_path):
    from fastapi import UploadFile
    from io import BytesIO
    monkeypatch.setattr(settings,'AUDIO_TEMP_DIR',str(tmp_path))
    def fail(path):
        assert Path(path).exists()
        raise RuntimeError('transcription failed')
    monkeypatch.setattr(speech,'_transcribe_path',fail)
    with pytest.raises(RuntimeError):
        await speech.transcribe_audio(UploadFile(filename='../../untrusted.wav',file=BytesIO(b'audio')))
    assert not list(tmp_path.iterdir())


def follow_up():
    return {"conversational_reply": "ok", "is_emergency": False,
            **{key: None for key in llm.CARE_SYSTEMS}}


def complete_guidance():
    return {"conversational_reply": "Here are the four perspectives.", "is_emergency": False,
            **{key: {"summary": "Information", "evidence_level": "limited", "precautions": "Seek advice if worsening"}
               for key in llm.CARE_SYSTEMS}}


@pytest.mark.parametrize("raw", [
    '{"conversational_reply":"Here is guidance", "allopathic":',
    'Just a single plain-text output',
    json.dumps({"conversational_reply": "ok", "is_emergency": False}),
    json.dumps({**follow_up(), "allopathic": {"summary": "Only one card"}}),
])
def test_incomplete_responses_are_not_silently_flattened(raw):
    with pytest.raises(llm.InvalidLLMResponseError):
        llm._parse_response(raw)


def test_complete_guidance_and_clarification_are_preserved():
    for payload in (follow_up(), complete_guidance()):
        assert llm._parse_response(json.dumps(payload)) == payload
        assert llm._parse_response('```json\n'+json.dumps(payload)+'\n```') == payload


@pytest.mark.asyncio
async def test_invalid_response_retried_once_then_four_perspectives_returned(monkeypatch):
    monkeypatch.setattr(settings, 'LLM_PROVIDER', 'ollama')
    monkeypatch.setattr(llm, 'retrieve_context_with_sources', lambda _: {'context':'','sources':[]})
    provider=AsyncMock(side_effect=[llm.InvalidLLMResponseError('truncated'), complete_guidance()])
    monkeypatch.setattr(llm, '_chat_ollama', provider)
    result=await llm.chat_completion('symptom details','hi',[])
    assert provider.await_count == 2
    assert all(isinstance(result[key],dict) for key in llm.CARE_SYSTEMS)
    assert provider.call_args_list[0] == provider.call_args_list[1]
    provider.reset_mock(side_effect=True)
    provider.side_effect=llm.InvalidLLMResponseError('still invalid')
    with pytest.raises(llm.InvalidLLMResponseError):
        await llm.chat_completion('symptom details')
    assert provider.await_count == 2


@pytest.mark.asyncio
async def test_ollama_preserves_default_generation_budget(monkeypatch):
    response=SimpleNamespace(raise_for_status=lambda:None,json=lambda:{'message':{'content':json.dumps(complete_guidance())}})
    client=SimpleNamespace(is_closed=False,post=AsyncMock(return_value=response))
    monkeypatch.setattr(llm,'_http_client',client)
    result=await llm._chat_ollama('details','en','',[])
    assert all(result[key] for key in llm.CARE_SYSTEMS)
    assert 'options' not in client.post.call_args.kwargs['json']
