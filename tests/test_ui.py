"""Browser regressions. Start the app on :8765, then run this file explicitly.
Requires: pip install playwright; playwright install chromium
"""
import asyncio
import os
import pytest

playwright = pytest.importorskip('playwright.async_api')
BASE_URL = os.getenv('SWASTHAI_TEST_URL')
pytestmark = pytest.mark.skipif(not BASE_URL, reason='Set SWASTHAI_TEST_URL to run browser checks')


@pytest.mark.asyncio
async def test_theme_toggle_persists_and_remedy_cards_lift_on_hover():
        async with playwright.async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True, args=['--no-sandbox'])
                page = await browser.new_page(viewport={'width':1280,'height':900})
                await page.goto(BASE_URL)
                toggle = page.locator('#theme-toggle')
                initial_theme = await page.locator('html').get_attribute('data-theme')
                await toggle.click()
                selected_theme = await page.locator('html').get_attribute('data-theme')
                assert selected_theme != initial_theme
                assert await toggle.get_attribute('aria-pressed') == str(selected_theme == 'dark').lower()
                await page.reload()
                assert await page.locator('html').get_attribute('data-theme') == selected_theme

                await page.evaluate('''() => {
                    document.querySelector('#remedies').hidden = false;
                    document.querySelector('#remedy-grid').innerHTML = '<article class="remedy-card"><h4>Allopathic</h4><p>Test guidance</p></article>';
                }''')
                card = page.locator('.remedy-card')
                await card.hover()
                await page.wait_for_function("getComputedStyle(document.querySelector('.remedy-card')).transform !== 'none'")
                assert await card.evaluate("el => getComputedStyle(el).transform") != 'none'
                await browser.close()


@pytest.mark.asyncio
async def test_locales_chat_recording_and_mobile(tmp_path):
    async with playwright.async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page(viewport={'width':1280,'height':900})
        errors=[]
        page.on('pageerror',lambda error: errors.append(str(error)))
        await page.add_init_script('''
            window.speechSynthesis.cancel = () => {};
            window.speechSynthesis.speak = () => {};
            navigator.mediaDevices.getUserMedia = async () => ({getTracks:()=>[{stop:()=>{}}]});
            window.MediaRecorder = class extends EventTarget {
                constructor(){ super(); this.state='inactive'; this.mimeType='audio/webm'; }
                start(){ this.state='recording'; }
                stop(){
                    this.state='inactive';
                    const data=new Event('dataavailable'); data.data=new Blob(['audio']);
                    this.dispatchEvent(data); this.dispatchEvent(new Event('stop'));
                }
            };
        ''')
        await page.goto(BASE_URL)
        locales=await page.evaluate('Object.keys(window.SWASTHAI_I18N)')
        for locale in locales:
            await page.select_option('#language',locale)
            assert await page.get_attribute('html','lang')==locale
            assert await page.get_attribute('html','dir')==('rtl' if locale=='ur' else 'ltr')
            assert await page.evaluate('''() => [...document.querySelectorAll('[data-i18n]')].every(el => el.textContent===SWASTHAI_I18N[document.documentElement.lang][el.dataset.i18n])''')
            assert await page.get_attribute('#record-button','title')==await page.evaluate(f'SWASTHAI_I18N.{locale}.speak')
        await page.select_option('#language','hi')
        await page.reload()
        assert await page.input_value('#language')=='hi'
        pending=asyncio.Event()
        calls=[]
        async def chat(route):
            calls.append(route.request.post_data)
            await pending.wait()
            remedy={'summary':'Test guidance','precautions':'Seek care if worse','evidence_level':'moderate'}
            await route.fulfill(json={
                'conversational_reply':'आपकी जानकारी के आधार पर सामान्य सुझाव।',
                'follow_up_question':'क्या आपको बुखार भी है?',
                'is_emergency':False,'language':'hi',
                'allopathic':remedy,'ayurvedic':remedy,'unani':remedy,'homeopathic':remedy,
            })
        await page.route('**/chat',chat)
        await page.fill('#message','Mild headache')
        await page.click('.send-button')
        assert await page.is_visible('.chat-message.user')
        assert await page.is_disabled('.send-button')
        assert await page.is_disabled('#new-question')
        await page.select_option('#language','ta')
        assert 'தயாராகிறது' in await page.inner_text('#record-status')
        pending.set()
        await page.wait_for_selector('.chat-message.assistant')
        assert len(calls)==1
        assert await page.locator('.remedy-card').count()==4
        assert await page.is_visible('#follow-up-box')
        assert await page.inner_text('#follow-up-question')=='क्या आपको बुखार भी है?'
        assert await page.locator('#remedy-grid').evaluate("el => !!(el.compareDocumentPosition(document.querySelector('#follow-up-box')) & Node.DOCUMENT_POSITION_FOLLOWING)")
        assert await page.input_value('#message')==''
        await page.wait_for_function("!document.querySelector('.send-button').disabled")
        await page.fill('#message','No fever')
        await page.click('.send-button')
        await page.wait_for_function("!document.querySelector('.send-button').disabled")
        assert len(calls)==2
        assert 'क्या आपको बुखार भी है?' in calls[1]
        await page.unroute('**/chat')
        await page.route('**/chat',lambda route:route.fulfill(status=502,json={'error':'English server error'}))
        await page.fill('#message','retry me')
        await page.click('.send-button')
        await page.wait_for_selector('#error-message:not([hidden])')
        assert await page.input_value('#message')=='retry me'
        assert 'English' not in await page.inner_text('#error-message')
        assert await page.locator('.chat-message.user').count()==2
        await page.click('#new-question')
        await page.select_option('#language','ur')
        await page.set_viewport_size({'width':390,'height':844})
        assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        voice=[]
        async def respond_voice(route):
            voice.append(route.request.post_data_buffer)
            await route.fulfill(json={
                'transcribed_text':'A spoken question','detected_language':'en','language':'ur',
                'conversational_reply':'یہ عمومی رہنمائی ہے۔','follow_up_question':'کیا آپ کو بخار ہے؟','is_emergency':False,
                'allopathic':{'summary':'طبی مشورہ','precautions':'احتیاط','evidence_level':'strong'},
                'sources':[{'source_url':'https://www.nhs.uk/conditions/dehydration/'}],
            })
        await page.route('**/voice-chat',respond_voice)
        await page.click('#record-button')
        await page.wait_for_function("document.querySelector('#record-button').getAttribute('aria-pressed')==='true'")
        assert await page.is_visible('.stop-icon')
        assert await page.is_disabled('.send-button')
        await page.click('#record-button')
        await page.wait_for_selector('.remedy-card')
        assert b'name="language"\r\n\r\nur' in voice[0]
        assert await page.is_visible('.mic-icon')
        assert await page.locator('#sources a').count()==1
        assert 'مضبوط' in await page.inner_text('.evidence')
        await page.evaluate('document.fonts.ready')
        await page.screenshot(path=str(tmp_path / 'urdu-mobile.png'),full_page=True)
        await page.screenshot(path='/tmp/swasthai-urdu-mobile.png',full_page=True)
        await page.select_option('#language','en')
        assert 'Modern medicine' in await page.inner_text('.remedy-card h4')
        await page.set_viewport_size({'width':1280,'height':900})
        await page.click('#new-question')
        await page.screenshot(path='/tmp/swasthai-desktop.png',full_page=True)
        assert not errors,errors
        await browser.close()
