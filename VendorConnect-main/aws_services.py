"""
VendorConnect - AWS Services Integration
=========================================
Centralised wrappers for every AWS service used in this project.

Services:
  • S3           – Media / image / document storage
  • SNS           – SMS OTP & push notifications
  • Amazon Polly  – Text-to-Speech (12 Indian languages)
  • Amazon Transcribe – Speech-to-Text
  • Amazon Translate  – Real-time UI translation (12 Indian languages)
  • Amazon Rekognition – Supplier document / image verification
  • SQS           – Group-order event queue (Lambda-compatible)

All clients are lazily initialised so the app boots even without AWS
credentials configured (a warning is logged instead of an exception).
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Optional, Tuple

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

# ── Load env ──────────────────────────────────────────────────────────────────
_env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=_env_path)

logger = logging.getLogger(__name__)

# ── AWS Configuration ─────────────────────────────────────────────────────────
AWS_REGION        = os.environ.get('AWS_REGION', 'ap-south-1')   # Mumbai
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_KEY    = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
S3_BUCKET_NAME    = os.environ.get('AWS_S3_BUCKET', 'vendorconnect-media')
SNS_SMS_SENDER_ID = os.environ.get('AWS_SNS_SENDER_ID', 'VendorConn')
SQS_GROUP_ORDER_URL = os.environ.get('AWS_SQS_GROUP_ORDER_URL', '')


def _make_client(service: str):
    """Create a boto3 client; returns None if credentials are absent."""
    key = AWS_ACCESS_KEY_ID
    secret = AWS_SECRET_KEY
    if not key or not secret:
        logger.warning(
            'AWS credentials not configured – %s client will be unavailable. '
            'Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env.',
            service,
        )
        return None
    try:
        return boto3.client(
            service,
            region_name=AWS_REGION,
            aws_access_key_id=key,
            aws_secret_access_key=secret,
        )
    except Exception as exc:
        logger.exception('Failed to create %s client: %s', service, exc)
        return None


# Lazily-initialised singletons
_s3_client          = None
_sns_client         = None
_polly_client       = None
_transcribe_client  = None
_translate_client   = None
_rekognition_client = None
_sqs_client         = None


def get_s3():
    global _s3_client
    if _s3_client is None:
        _s3_client = _make_client('s3')
    return _s3_client


def get_sns():
    global _sns_client
    if _sns_client is None:
        _sns_client = _make_client('sns')
    return _sns_client


def get_polly():
    global _polly_client
    if _polly_client is None:
        _polly_client = _make_client('polly')
    return _polly_client


def get_transcribe():
    global _transcribe_client
    if _transcribe_client is None:
        _transcribe_client = _make_client('transcribe')
    return _transcribe_client


def get_translate():
    global _translate_client
    if _translate_client is None:
        _translate_client = _make_client('translate')
    return _translate_client


def get_rekognition():
    global _rekognition_client
    if _rekognition_client is None:
        _rekognition_client = _make_client('rekognition')
    return _rekognition_client


def get_sqs():
    global _sqs_client
    if _sqs_client is None:
        _sqs_client = _make_client('sqs')
    return _sqs_client


# ─────────────────────────────────────────────────────────────────────────────
# S3 – Media Storage
# ─────────────────────────────────────────────────────────────────────────────

def upload_file_to_s3(
    file_bytes: bytes,
    filename: str,
    content_type: str = 'application/octet-stream',
    folder: str = 'uploads',
) -> Optional[str]:
    """Upload bytes to S3 and return the public URL, or None on failure."""
    client = get_s3()
    if client is None:
        logger.warning('S3 unavailable – falling back to local storage.')
        return None
    key = f'{folder}/{filename}'
    try:
        client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
            ACL='public-read',
        )
        url = f'https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}'
        logger.info('Uploaded to S3: %s', url)
        return url
    except ClientError as exc:
        logger.exception('S3 upload failed: %s', exc)
        return None


def upload_image_to_s3(file_storage, folder: str = 'images') -> Optional[str]:
    """Upload a Werkzeug FileStorage image to S3."""
    if file_storage is None or not file_storage.filename:
        return None
    ext = file_storage.filename.rsplit('.', 1)[-1].lower()
    unique_name = f'{uuid.uuid4().hex}.{ext}'
    content_type = file_storage.content_type or f'image/{ext}'
    file_bytes = file_storage.read()
    return upload_file_to_s3(file_bytes, unique_name, content_type, folder)


def get_presigned_url(key: str, expiry: int = 3600) -> Optional[str]:
    """Return a pre-signed download URL for a private S3 object."""
    client = get_s3()
    if client is None:
        return None
    try:
        return client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': key},
            ExpiresIn=expiry,
        )
    except ClientError as exc:
        logger.exception('Presigned URL error: %s', exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# SNS – SMS OTP & Notifications
# ─────────────────────────────────────────────────────────────────────────────

def send_sms_otp(phone_number: str, otp: str, language: str = 'en') -> bool:
    """
    Send OTP via AWS SNS SMS.
    phone_number must be E.164 format, e.g. +919876543210
    Returns True on success, False on failure.
    """
    client = get_sns()
    if client is None:
        logger.warning('SNS unavailable – OTP not sent via SMS.')
        return False

    # Normalise phone number to E.164 for India
    number = phone_number.strip()
    if number.startswith('0'):
        number = '+91' + number[1:]
    elif not number.startswith('+'):
        number = '+91' + number

    otp_messages = {
        'hi': f'आपका VendorConnect OTP है: {otp}. 10 मिनट में वैध।',
        'mr': f'तुमचा VendorConnect OTP: {otp}. 10 मिनिटांत वैध.',
        'ta': f'உங்கள் VendorConnect OTP: {otp}. 10 நிமிடங்களில் செல்லுபடியாகும்.',
        'te': f'మీ VendorConnect OTP: {otp}. 10 నిమిషాల్లో చెల్లుతుంది.',
        'bn': f'আপনার VendorConnect OTP: {otp}। 10 মিনিটে বৈধ।',
        'gu': f'તમારો VendorConnect OTP: {otp}. 10 મિનિટ માટે માન્ય.',
        'kn': f'ನಿಮ್ಮ VendorConnect OTP: {otp}. 10 ನಿಮಿಷದಲ್ಲಿ ಮಾನ್ಯ.',
        'ml': f'നിങ്ങളുടെ VendorConnect OTP: {otp}. 10 മിനിറ്റ് സാധുത.',
        'pa': f'ਤੁਹਾਡਾ VendorConnect OTP: {otp}। 10 ਮਿੰਟ ਲਈ ਵੈਧ.',
        'or': f'ଆପଣଙ୍କ VendorConnect OTP: {otp}। 10 ମିନିଟ ବୈଧ.',
        'as': f'আপোনাৰ VendorConnect OTP: {otp}। ১০ মিনিটত বৈধ.',
        'en': f'Your VendorConnect OTP is: {otp}. Valid for 10 minutes.',
    }
    message = otp_messages.get(language, otp_messages['en'])

    try:
        client.publish(
            PhoneNumber=number,
            Message=message,
            MessageAttributes={
                'AWS.SNS.SMS.SenderID': {
                    'DataType': 'String',
                    'StringValue': SNS_SMS_SENDER_ID,
                },
                'AWS.SNS.SMS.SMSType': {
                    'DataType': 'String',
                    'StringValue': 'Transactional',
                },
            },
        )
        logger.info('OTP SMS sent to %s', number)
        return True
    except ClientError as exc:
        logger.exception('SNS SMS send failed: %s', exc)
        return False


def send_order_notification_sms(phone_number: str, message: str) -> bool:
    """Send a generic order notification SMS."""
    client = get_sns()
    if client is None:
        return False
    number = phone_number.strip()
    if not number.startswith('+'):
        number = '+91' + number
    try:
        client.publish(
            PhoneNumber=number,
            Message=message,
            MessageAttributes={
                'AWS.SNS.SMS.SMSType': {
                    'DataType': 'String',
                    'StringValue': 'Transactional',
                },
            },
        )
        return True
    except ClientError as exc:
        logger.exception('SNS order notification failed: %s', exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Amazon Polly – Text-to-Speech (12 Indian Languages)
# ─────────────────────────────────────────────────────────────────────────────

# Polly voice IDs for each supported language
POLLY_VOICES = {
    'hi': 'Aditi',       # Hindi (India) – neural
    'en': 'Raveena',     # English (India)
    'ta': 'Kajal',       # Tamil (India) – neural
    'te': 'Aditi',       # Telugu → use Hindi voice (Polly limitation)
    'bn': 'Aditi',       # Bengali → fallback
    'mr': 'Aditi',       # Marathi → fallback Hindi
    'gu': 'Aditi',       # Gujarati → fallback
    'kn': 'Kajal',       # Kannada → Tamil voice
    'ml': 'Aditi',       # Malayalam → fallback
    'pa': 'Aditi',       # Punjabi → fallback
    'or': 'Aditi',       # Odia → fallback
    'as': 'Aditi',       # Assamese → fallback
}

POLLY_LANGUAGE_CODES = {
    'hi': 'hi-IN',
    'en': 'en-IN',
    'ta': 'ta-IN',
    'te': 'hi-IN',
    'bn': 'hi-IN',
    'mr': 'hi-IN',
    'gu': 'hi-IN',
    'kn': 'ta-IN',
    'ml': 'hi-IN',
    'pa': 'hi-IN',
    'or': 'hi-IN',
    'as': 'hi-IN',
}


def text_to_speech(text: str, language: str = 'en') -> Optional[bytes]:
    """
    Convert text to speech using Amazon Polly.
    Returns MP3 audio bytes, or None on failure.
    """
    client = get_polly()
    if client is None:
        return None

    voice_id = POLLY_VOICES.get(language, 'Raveena')
    # Kajal (ta-IN) supports neural; Aditi & Raveena are standard-only
    NEURAL_VOICES = {'Kajal'}
    engine = 'neural' if voice_id in NEURAL_VOICES else 'standard'

    try:
        response = client.synthesize_speech(
            Text=text[:2900],          # Polly limit is 3000 chars
            OutputFormat='mp3',
            VoiceId=voice_id,
            Engine=engine,
            LanguageCode=POLLY_LANGUAGE_CODES.get(language, 'hi-IN'),
        )
        audio_stream = response.get('AudioStream')
        if audio_stream:
            return audio_stream.read()
    except ClientError as exc:
        error_code = exc.response['Error']['Code']
        if error_code == 'EngineNotSupportedException':
            # Retry with standard engine
            try:
                response = client.synthesize_speech(
                    Text=text[:2900],
                    OutputFormat='mp3',
                    VoiceId=voice_id,
                    Engine='standard',
                    LanguageCode=POLLY_LANGUAGE_CODES.get(language, 'hi-IN'),
                )
                audio_stream = response.get('AudioStream')
                if audio_stream:
                    return audio_stream.read()
            except ClientError as inner_exc:
                logger.exception('Polly TTS retry failed: %s', inner_exc)
        else:
            logger.exception('Polly TTS error: %s', exc)
    return None


def text_to_speech_base64(text: str, language: str = 'en') -> Optional[str]:
    """Return base64-encoded MP3 string (for JSON API responses)."""
    audio_bytes = text_to_speech(text, language)
    if audio_bytes:
        return base64.b64encode(audio_bytes).decode('utf-8')
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Amazon Transcribe – Speech-to-Text
# ─────────────────────────────────────────────────────────────────────────────

TRANSCRIBE_LANGUAGE_CODES = {
    'hi': 'hi-IN',
    'en': 'en-IN',
    'ta': 'ta-IN',
    'te': 'te-IN',
    'bn': 'bn-IN',
    'mr': 'mr-IN',
    'gu': 'gu-IN',
    'kn': 'kn-IN',
    'ml': 'ml-IN',
    'pa': 'pa-IN',
    'or': 'hi-IN',   # Odia not yet supported – use Hindi fallback
    'as': 'hi-IN',   # Assamese not yet supported
}


def transcribe_audio_bytes(
    audio_bytes: bytes,
    language: str = 'hi',
    audio_format: str = 'webm',
) -> Optional[str]:
    """
    Transcribe audio bytes via Amazon Transcribe Streaming.
    Returns the transcript string or None on failure.

    For browser recordings (WebM/OGG), we upload to S3 first then start
    a standard (non-streaming) transcription job.
    """
    s3 = get_s3()
    transcribe = get_transcribe()
    if s3 is None or transcribe is None:
        logger.warning('Transcribe or S3 unavailable.')
        return None

    lang_code = TRANSCRIBE_LANGUAGE_CODES.get(language, 'hi-IN')
    job_name  = f'vc-{uuid.uuid4().hex}'
    s3_key    = f'transcribe-input/{job_name}.{audio_format}'

    # Upload audio to S3
    mime_map = {
        'webm': 'audio/webm',
        'ogg':  'audio/ogg',
        'wav':  'audio/wav',
        'mp3':  'audio/mpeg',
        'mp4':  'audio/mp4',
        'flac': 'audio/flac',
    }
    content_type = mime_map.get(audio_format, 'audio/webm')
    try:
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=audio_bytes,
            ContentType=content_type,
        )
    except ClientError as exc:
        logger.exception('S3 upload for Transcribe failed: %s', exc)
        return None

    media_uri = f's3://{S3_BUCKET_NAME}/{s3_key}'

    # Start transcription job
    try:
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': media_uri},
            MediaFormat=audio_format if audio_format in ('mp3', 'mp4', 'wav', 'flac', 'ogg', 'webm') else 'webm',
            LanguageCode=lang_code,
        )
    except ClientError as exc:
        logger.exception('Transcribe job start failed: %s', exc)
        return None

    # Poll for completion (max 30 seconds for short audio)
    for _ in range(30):
        time.sleep(1)
        try:
            status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            state  = status['TranscriptionJob']['TranscriptionJobStatus']
            if state == 'COMPLETED':
                transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
                import urllib.request
                with urllib.request.urlopen(transcript_uri) as resp:
                    result = json.load(resp)
                transcript = result['results']['transcripts'][0]['transcript']
                # Clean up S3 input file
                try:
                    s3.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
                except Exception:
                    pass
                return transcript
            elif state == 'FAILED':
                logger.error('Transcription job failed: %s', status)
                return None
        except ClientError as exc:
            logger.exception('Polling transcription job: %s', exc)
            return None

    logger.warning('Transcription job timed out: %s', job_name)
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Amazon Translate – Real-time UI Translation
# ─────────────────────────────────────────────────────────────────────────────

# Map our short codes to AWS Translate language codes
TRANSLATE_LANG_MAP = {
    'hi': 'hi',   # Hindi
    'en': 'en',   # English
    'ta': 'ta',   # Tamil
    'te': 'te',   # Telugu
    'bn': 'bn',   # Bengali
    'mr': 'mr',   # Marathi
    'gu': 'gu',   # Gujarati
    'kn': 'kn',   # Kannada
    'ml': 'ml',   # Malayalam
    'pa': 'pa',   # Punjabi
    'or': 'or',   # Odia
    'as': 'as',   # Assamese
}

LANGUAGE_NAMES = {
    'en': 'English',
    'hi': 'हिंदी',
    'mr': 'मराठी',
    'ta': 'தமிழ்',
    'te': 'తెలుగు',
    'bn': 'বাংলা',
    'gu': 'ગુજરાતી',
    'kn': 'ಕನ್ನಡ',
    'ml': 'മലയാളം',
    'pa': 'ਪੰਜਾਬੀ',
    'or': 'ଓଡ଼ିଆ',
    'as': 'অসমীয়া',
}


def translate_text(text: str, target_language: str, source_language: str = 'auto') -> str:
    """
    Translate text using Amazon Translate.
    Returns translated text, or original text on failure.
    """
    if not text or not text.strip():
        return text

    client = get_translate()
    if client is None:
        return text   # Graceful degradation

    target = TRANSLATE_LANG_MAP.get(target_language, target_language)
    source = 'auto' if source_language == 'auto' else TRANSLATE_LANG_MAP.get(source_language, source_language)

    try:
        response = client.translate_text(
            Text=text[:10000],
            SourceLanguageCode=source,
            TargetLanguageCode=target,
        )
        return response['TranslatedText']
    except ClientError as exc:
        logger.exception('Translation error: %s', exc)
        return text


def translate_batch(texts: list[str], target_language: str) -> list[str]:
    """Translate a list of strings (each call is sequential to keep order)."""
    return [translate_text(t, target_language) for t in texts]


# ─────────────────────────────────────────────────────────────────────────────
# Amazon Rekognition – Supplier Verification
# ─────────────────────────────────────────────────────────────────────────────

# Keywords that indicate a valid business/certification document
VALID_DOC_KEYWORDS = {
    'gstin', 'gst', 'registration', 'certificate', 'license', 'fssai',
    'food', 'safety', 'authority', 'trade', 'shop', 'act', 'municipal',
    'corporation', 'government', 'india', 'certified', 'approved',
    'permit', 'vendor', 'supplier', 'business',
}

# Labels that suggest a genuine document scan
VALID_DOC_LABELS = {
    'document', 'text', 'paper', 'certificate', 'id card',
    'business card', 'form', 'receipt', 'invoice',
}


def verify_supplier_document(image_bytes: bytes) -> dict:
    """
    Use Rekognition to verify a supplier's certification document.

    Returns a dict:
      {
        'verified': bool,
        'confidence': float,  # 0-100
        'detected_text': [str],
        'labels': [str],
        'reason': str
      }
    """
    client = get_rekognition()
    if client is None:
        return {
            'verified': False,
            'confidence': 0.0,
            'detected_text': [],
            'labels': [],
            'reason': 'Rekognition service unavailable',
        }

    image_obj = {'Bytes': image_bytes}
    detected_text_items = []
    label_names = []
    score = 0.0

    # 1. Detect text
    try:
        text_response = client.detect_text(Image=image_obj)
        for item in text_response.get('TextDetections', []):
            if item['Type'] == 'LINE' and item['Confidence'] > 60:
                detected_text_items.append(item['DetectedText'])
    except ClientError as exc:
        logger.exception('Rekognition detect_text failed: %s', exc)

    # 2. Detect labels (what's in the image)
    try:
        label_response = client.detect_labels(Image=image_obj, MaxLabels=15, MinConfidence=60)
        label_names = [lbl['Name'].lower() for lbl in label_response.get('Labels', [])]
    except ClientError as exc:
        logger.exception('Rekognition detect_labels failed: %s', exc)

    # 3. Moderation check – reject inappropriate images
    try:
        mod_response = client.detect_moderation_labels(Image=image_obj, MinConfidence=70)
        if mod_response.get('ModerationLabels'):
            return {
                'verified': False,
                'confidence': 0.0,
                'detected_text': detected_text_items,
                'labels': label_names,
                'reason': 'Image contains inappropriate content',
            }
    except ClientError as exc:
        logger.exception('Rekognition moderation check failed: %s', exc)

    # 4. Score the document
    all_text = ' '.join(detected_text_items).lower()

    keyword_hits = sum(1 for kw in VALID_DOC_KEYWORDS if kw in all_text)
    label_hits   = sum(1 for lbl in VALID_DOC_LABELS if lbl in ' '.join(label_names))

    has_numbers   = any(c.isdigit() for c in all_text)
    has_text      = len(detected_text_items) >= 3

    # Calculate confidence score
    score = min(100.0, (keyword_hits * 15) + (label_hits * 10) + (10 if has_numbers else 0) + (10 if has_text else 0))

    verified = score >= 30 and has_text

    reason = 'Document appears valid' if verified else (
        'No recognisable document text detected – please upload a clear scan of your GSTIN/FSSAI certificate.'
    )

    return {
        'verified': verified,
        'confidence': round(score, 1),
        'detected_text': detected_text_items[:20],  # trim for JSON size
        'labels': label_names[:10],
        'reason': reason,
    }


def analyze_food_image(image_bytes: bytes) -> dict:
    """
    Analyse a product/food image using Rekognition.
    Returns detected food labels and safety check.
    """
    client = get_rekognition()
    if client is None:
        return {'safe': True, 'labels': [], 'food_detected': False}

    image_obj = {'Bytes': image_bytes}
    labels    = []
    food_detected = False

    try:
        response = client.detect_labels(Image=image_obj, MaxLabels=20, MinConfidence=70)
        labels = [lbl['Name'] for lbl in response.get('Labels', [])]
        food_keywords = {'food', 'meal', 'dish', 'cuisine', 'vegetable', 'fruit', 'spice', 'ingredient'}
        food_detected  = any(lbl.lower() in food_keywords or any(fw in lbl.lower() for fw in food_keywords) for lbl in labels)
    except ClientError as exc:
        logger.exception('Food image analysis failed: %s', exc)

    # Moderation
    safe = True
    try:
        mod = client.detect_moderation_labels(Image=image_obj, MinConfidence=70)
        safe = len(mod.get('ModerationLabels', [])) == 0
    except ClientError:
        pass

    return {'safe': safe, 'labels': labels, 'food_detected': food_detected}


# ─────────────────────────────────────────────────────────────────────────────
# SQS – Group Order Event Queue
# ─────────────────────────────────────────────────────────────────────────────

def publish_group_order_event(event_type: str, payload: dict) -> bool:
    """
    Send a group-order event to SQS for async processing.
    event_type: 'VENDOR_JOINED' | 'ORDER_COMPLETED' | 'ORDER_EXPIRED' | 'CREATED'
    Returns True on success.
    """
    client = get_sqs()
    if client is None or not SQS_GROUP_ORDER_URL:
        logger.warning('SQS unavailable or queue URL not configured – event not published.')
        return False

    message = {
        'event_type': event_type,
        'timestamp':  int(time.time()),
        **payload,
    }

    try:
        client.send_message(
            QueueUrl=SQS_GROUP_ORDER_URL,
            MessageBody=json.dumps(message),
            MessageAttributes={
                'EventType': {
                    'DataType': 'String',
                    'StringValue': event_type,
                }
            },
        )
        logger.info('SQS event published: %s', event_type)
        return True
    except ClientError as exc:
        logger.exception('SQS publish failed: %s', exc)
        return False


def lambda_group_order_handler(event: dict, context=None) -> dict:
    """
    AWS Lambda-compatible handler for processing SQS group-order events.
    Can also be called directly from a scheduled task.

    Expects the SQS event format:
      { "Records": [{ "body": "<json-string>", ... }] }

    Or can be called directly with a single record dict.
    """
    records = event.get('Records', [event])
    processed = 0

    for record in records:
        try:
            body = record.get('body', '')
            if isinstance(body, str):
                data = json.loads(body)
            else:
                data = body

            event_type    = data.get('event_type', '')
            group_order_id = data.get('group_order_id')

            logger.info('Processing SQS event: %s for group_order %s', event_type, group_order_id)

            if event_type == 'VENDOR_JOINED':
                _handle_vendor_joined(data)
            elif event_type == 'ORDER_COMPLETED':
                _handle_order_completed(data)
            elif event_type == 'ORDER_EXPIRED':
                _handle_order_expired(data)
            elif event_type == 'CREATED':
                _handle_order_created(data)

            processed += 1
        except Exception as exc:
            logger.exception('Error processing SQS record: %s', exc)

    return {'statusCode': 200, 'processed': processed}


def _handle_vendor_joined(data: dict):
    """Notify existing participants when a new vendor joins."""
    logger.info('[SQS] Vendor %s joined group order %s', data.get('vendor_id'), data.get('group_order_id'))
    # Notification dispatch would go here (SNS / push)


def _handle_order_completed(data: dict):
    """Notify all participants that the group order has been fulfilled."""
    logger.info('[SQS] Group order %s completed', data.get('group_order_id'))
    participants = data.get('participant_phones', [])
    for phone in participants:
        send_order_notification_sms(
            phone,
            f"VendorConnect: Your group order #{data.get('group_order_id')} has been confirmed! "
            "Check the app for delivery details.",
        )


def _handle_order_expired(data: dict):
    """Notify participants that the group order expired."""
    logger.info('[SQS] Group order %s expired', data.get('group_order_id'))
    participants = data.get('participant_phones', [])
    for phone in participants:
        send_order_notification_sms(
            phone,
            f"VendorConnect: Group order #{data.get('group_order_id')} expired without meeting "
            "minimum quantity. You can place an individual order instead.",
        )


def _handle_order_created(data: dict):
    logger.info('[SQS] New group order %s created for product %s', data.get('group_order_id'), data.get('product_name'))
