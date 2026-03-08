"""
One-shot AWS feature audit. Run:  python audit_aws.py
"""
import json, io, sys, os
os.environ.setdefault('FLASK_ENV', 'testing')

from app import app, db

def chk(label, code, body):
    if isinstance(body, dict):
        detail = (body.get('translated_text') or body.get('message') or
                  body.get('error') or body.get('otp_fallback') or str(body)[:90])
        ok = "✅" if code == 200 and body.get('success') != False else "❌"
    elif isinstance(body, str):
        detail = body[:90]
        ok = "✅" if code == 200 else "❌"
    else:
        detail = str(body)[:90]
        ok = "✅" if code == 200 else "❌"
    print(f"  {ok}  {label:42s} HTTP {code}  —  {detail}")

print("\n======  VendorConnect AWS Feature Audit  ======\n")

with app.app_context():
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['vendor_id'] = 1

        # ── SQS ──────────────────────────────────────────────────────
        r = c.post('/api/create-group-order',
            json={'product_name':'audit_test','target_quantity':10,'price_per_unit':20},
            content_type='application/json')
        chk("SQS  /api/create-group-order", r.status_code, r.get_json())

        orders = c.get('/api/group-orders').get_json()
        unjoined = next((o for o in reversed(orders) if not o.get('is_joined')), None)
        if unjoined:
            r = c.post('/api/join-group-order',
                json={'group_order_id': unjoined['id'], 'quantity': 3},
                content_type='application/json')
            chk("SQS  /api/join-group-order", r.status_code, r.get_json())
        else:
            print("  ⚠️   SQS  /api/join-group-order             — no un-joined order available")

        r = c.post('/api/group-orders/process-expired')
        chk("SQS  /api/group-orders/process-expired", r.status_code, r.get_json())

        r = c.post('/api/group-orders/sqs-handler',
            json={'Records':[{'body': json.dumps({'event_type':'TEST','data':{}})}]},
            content_type='application/json')
        chk("SQS  /api/group-orders/sqs-handler", r.status_code, r.get_json())

        # ── Translate ─────────────────────────────────────────────────
        r = c.post('/api/translate',
            json={'text':'Hello World','target_language':'hi'},
            content_type='application/json')
        chk("Translate  /api/translate", r.status_code, r.get_json())

        r = c.get('/api/translate/languages')
        d = r.get_json()
        chk("Translate  /api/translate/languages", r.status_code,
            f"{len(d)} languages" if isinstance(d, list) else d)

        # ── SNS ───────────────────────────────────────────────────────
        r = c.post('/api/sms/send-otp',
            json={'phone':'9999999999'}, content_type='application/json')
        chk("SNS  /api/sms/send-otp", r.status_code, r.get_json())

        r = c.post('/vendor/forgot-password',
            json={'phone':'9999999999','method':'phone'},
            content_type='application/json')
        chk("SNS  /vendor/forgot-password", r.status_code, r.get_json())

        # ── Polly ─────────────────────────────────────────────────────
        r = c.post('/api/voice/speak',
            json={'text':'Test speech','language':'en'},
            content_type='application/json')
        if r.content_type and 'json' in r.content_type:
            chk("Polly  /api/voice/speak", r.status_code, r.get_json())
        else:
            print(f"  ✅  Polly  /api/voice/speak                     HTTP {r.status_code}  —  audio returned ({len(r.data)} bytes, {r.content_type})")

        # ── Transcribe ────────────────────────────────────────────────
        r = c.post('/api/voice/transcribe',
            data={'audio': (io.BytesIO(b'RIFF\x00\x00\x00\x00WAVEfmt '), 'test.wav')},
            content_type='multipart/form-data')
        chk("Transcribe  /api/voice/transcribe", r.status_code, r.get_json())

        # ── Rekognition ───────────────────────────────────────────────
        fake_jpeg = (b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
                     + b'\xff\xd9')  # minimal valid JPEG
        r = c.post('/api/supplier/verify-document',
            data={'document': (io.BytesIO(fake_jpeg), 'doc.jpg')},
            content_type='multipart/form-data')
        chk("Rekognition  /api/supplier/verify-document", r.status_code, r.get_json())

        r = c.post('/api/product/analyze-image',
            data={'image': (io.BytesIO(fake_jpeg), 'food.jpg')},
            content_type='multipart/form-data')
        chk("Rekognition  /api/product/analyze-image", r.status_code, r.get_json())

print("\n===============================================\n")
