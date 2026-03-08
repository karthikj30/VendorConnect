"""
VendorConnect - AWS Services Integration
=========================================
Centralised wrappers for every AWS service used in this project.

Services:
  • S3              – Media / image / document storage
  • SNS             – SMS OTP & push notifications
  • Amazon Polly    – Text-to-Speech (12 Indian languages)
  • Amazon Transcribe – Speech-to-Text
  • Amazon Translate  – Real-time UI translation (12 Indian languages)
  • Amazon Rekognition – Supplier document / image verification
  • SQS             – Group-order event queue (Lambda-compatible)
  • Comprehend      – Sentiment analysis on customer reviews
  • SES             – Transactional email
  • Textract        – Document field extraction (GSTIN/FSSAI)
  • DynamoDB        – Real-time chat messages & live notifications
  • Lambda          – Invoke serverless functions
  • EventBridge     – Schedule / trigger events (order expiry, reports)
  • Location Service– Route optimisation & delivery geofencing
  • Personalize     – ML-based product recommendations
  • Cognito         – Managed user authentication with MFA

All clients are lazily initialised so the app boots even without AWS
credentials configured (a warning is logged instead of an exception).
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
import re
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
_s3_client           = None
_sns_client          = None
_polly_client        = None
_transcribe_client   = None
_translate_client    = None
_rekognition_client  = None
_sqs_client          = None
_comprehend_client   = None
_ses_client          = None
_textract_client     = None
_dynamodb_client     = None
_dynamodb_resource   = None
_lambda_client       = None
_events_client       = None   # EventBridge
_location_client     = None
_personalize_client  = None   # Personalize runtime
_cognito_client      = None


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


def get_comprehend():
    global _comprehend_client
    if _comprehend_client is None:
        _comprehend_client = _make_client('comprehend')
    return _comprehend_client


def get_ses():
    global _ses_client
    if _ses_client is None:
        _ses_client = _make_client('ses')
    return _ses_client


def get_textract():
    global _textract_client
    if _textract_client is None:
        _textract_client = _make_client('textract')
    return _textract_client


def get_dynamodb():
    """Return a low-level DynamoDB client."""
    global _dynamodb_client
    if _dynamodb_client is None:
        _dynamodb_client = _make_client('dynamodb')
    return _dynamodb_client


def get_dynamodb_resource():
    """Return a high-level DynamoDB resource (Table objects)."""
    global _dynamodb_resource
    if _dynamodb_resource is None:
        key = AWS_ACCESS_KEY_ID
        secret = AWS_SECRET_KEY
        if not key or not secret:
            logger.warning('AWS credentials not configured – DynamoDB resource unavailable.')
            return None
        try:
            _dynamodb_resource = boto3.resource(
                'dynamodb',
                region_name=AWS_REGION,
                aws_access_key_id=key,
                aws_secret_access_key=secret,
            )
        except Exception as exc:
            logger.exception('Failed to create DynamoDB resource: %s', exc)
    return _dynamodb_resource


def get_lambda():
    global _lambda_client
    if _lambda_client is None:
        _lambda_client = _make_client('lambda')
    return _lambda_client


def get_events():
    """Return an EventBridge client."""
    global _events_client
    if _events_client is None:
        _events_client = _make_client('events')
    return _events_client


def get_location():
    global _location_client
    if _location_client is None:
        _location_client = _make_client('location')
    return _location_client


def get_personalize_runtime():
    """Return a Personalize Runtime client for recommendations."""
    global _personalize_client
    if _personalize_client is None:
        _personalize_client = _make_client('personalize-runtime')
    return _personalize_client


def get_cognito():
    global _cognito_client
    if _cognito_client is None:
        _cognito_client = _make_client('cognito-idp')
    return _cognito_client


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

    NOTE (India / DLT):
    TRAI requires all SMS senders in India to register on the DLT portal.
    Until the DLT Entity ID & Template ID are registered and added to the
    MessageAttributes, Indian carriers silently drop the SMS even when
    SNS returns HTTP 200.  To unblock during development:
      1. Register at https://www.ucc.gov.in or any telecom DLT portal.
      2. Add  AWS_SNS_DLT_ENTITY_ID  and  AWS_SNS_DLT_TEMPLATE_ID  to .env.
    Until then, the OTP is returned in the API response as 'otp_fallback'
    so the front-end can display it to the user.
    """
    client = get_sns()
    if client is None:
        logger.warning('SNS unavailable – OTP not sent via SMS.')
        return False

    # Normalise phone number to E.164 for India
    number = phone_number.strip()
    if number.startswith('0'):
        number = '+91' + number[1:]
    elif re.match(r'^\d{10}$', number):
        number = '+91' + number
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

    # Build message attributes — only add DLT fields if configured
    msg_attrs: dict = {
        'AWS.SNS.SMS.SMSType': {
            'DataType': 'String',
            'StringValue': 'Transactional',
        },
    }

    # DLT registration (mandatory for India delivery)
    dlt_entity_id   = os.environ.get('AWS_SNS_DLT_ENTITY_ID', '')
    dlt_template_id = os.environ.get('AWS_SNS_DLT_TEMPLATE_ID', '')
    if dlt_entity_id and dlt_template_id:
        msg_attrs['AWS.MM.SMS.EntityId']   = {'DataType': 'String', 'StringValue': dlt_entity_id}
        msg_attrs['AWS.MM.SMS.TemplateId'] = {'DataType': 'String', 'StringValue': dlt_template_id}
        msg_attrs['AWS.SNS.SMS.SenderID']  = {'DataType': 'String', 'StringValue': SNS_SMS_SENDER_ID}
        logger.info('DLT headers added for India SMS delivery')
    else:
        logger.warning(
            'AWS_SNS_DLT_ENTITY_ID / AWS_SNS_DLT_TEMPLATE_ID not set in .env. '
            'SMS will be silently dropped by Indian carriers (TRAI DLT requirement). '
            'Register at https://www.ucc.gov.in and add the IDs to .env.'
        )

    try:
        response = client.publish(
            PhoneNumber=number,
            Message=message,
            MessageAttributes=msg_attrs,
        )
        logger.info('OTP SMS dispatched to %s (MessageId=%s)', number, response.get('MessageId'))
        return True
    except ClientError as exc:
        logger.exception('SNS SMS send failed: %s', exc)
        return False


def send_order_notification_sms(phone_number: str, message: str, target_language: str = 'en') -> bool:
    """
    Send a generic order notification SMS.
    If target_language is not 'en', the message is first translated via Amazon Translate.
    """
    client = get_sns()
    if client is None:
        return False
    number = phone_number.strip()
    if not number.startswith('+'):
        number = '+91' + number

    # ── Auto-translate message if a regional language is requested ────────────
    final_message = message
    if target_language and target_language != 'en':
        try:
            # translate_text defined later in this module; import lazily via globals
            _tt = globals().get('translate_text')
            if _tt:
                translated = _tt(message, target_language=target_language)
                if translated:
                    final_message = translated
        except Exception as _te:
            logger.warning('SMS translation to %s failed – sending in English: %s', target_language, _te)

    try:
        client.publish(
            PhoneNumber=number,
            Message=final_message,
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
    participants     = data.get('participant_phones', [])
    target_language  = data.get('language', 'en')
    for phone in participants:
        send_order_notification_sms(
            phone,
            f"VendorConnect: Your group order #{data.get('group_order_id')} has been confirmed! "
            "Check the app for delivery details.",
            target_language=target_language,
        )


def _handle_order_expired(data: dict):
    """Notify participants that the group order expired."""
    logger.info('[SQS] Group order %s expired', data.get('group_order_id'))
    participants     = data.get('participant_phones', [])
    target_language  = data.get('language', 'en')
    for phone in participants:
        send_order_notification_sms(
            phone,
            f"VendorConnect: Group order #{data.get('group_order_id')} expired without meeting "
            "minimum quantity. You can place an individual order instead.",
            target_language=target_language,
        )


def _handle_order_created(data: dict):
    logger.info('[SQS] New group order %s created for product %s', data.get('group_order_id'), data.get('product_name'))


# ─────────────────────────────────────────────────────────────────────────────
# Comprehend – Sentiment Analysis
# ─────────────────────────────────────────────────────────────────────────────

def analyze_sentiment(text: str, language_code: str = 'en') -> dict:
    """
    Analyse the sentiment of a review text using Amazon Comprehend.
    Returns: { 'sentiment': 'POSITIVE'|'NEGATIVE'|'NEUTRAL'|'MIXED',
               'scores': { Positive, Negative, Neutral, Mixed } (0-1 floats),
               'emoji': '😊'|'😠'|'😐'|'🤔' }
    Falls back to { 'sentiment': 'NEUTRAL', ... } if Comprehend unavailable.
    """
    # Comprehend only supports a subset of language codes – map common ones
    SUPPORTED = {'en', 'es', 'fr', 'de', 'it', 'pt', 'ar', 'hi', 'ja', 'ko', 'zh', 'zh-TW'}
    lang = language_code if language_code in SUPPORTED else 'en'

    client = get_comprehend()
    if client is None or not text or len(text.strip()) < 5:
        return {'sentiment': 'NEUTRAL', 'scores': {}, 'emoji': '😐'}

    try:
        resp = client.detect_sentiment(Text=text[:4900], LanguageCode=lang)
        sentiment = resp.get('Sentiment', 'NEUTRAL')
        scores = resp.get('SentimentScore', {})
        emoji_map = {
            'POSITIVE': '😊',
            'NEGATIVE': '😠',
            'NEUTRAL': '😐',
            'MIXED': '🤔',
        }
        return {
            'sentiment': sentiment,
            'scores': {
                'positive': round(scores.get('Positive', 0), 3),
                'negative': round(scores.get('Negative', 0), 3),
                'neutral':  round(scores.get('Neutral', 0), 3),
                'mixed':    round(scores.get('Mixed', 0), 3),
            },
            'emoji': emoji_map.get(sentiment, '😐'),
        }
    except ClientError as exc:
        logger.exception('Comprehend sentiment analysis failed: %s', exc)
        return {'sentiment': 'NEUTRAL', 'scores': {}, 'emoji': '😐'}


# ─────────────────────────────────────────────────────────────────────────────
# SES – Transactional Email (replaces Gmail SMTP)
# ─────────────────────────────────────────────────────────────────────────────

SES_SENDER_EMAIL = os.environ.get('AWS_SES_SENDER_EMAIL', '')


def send_ses_email(to_email: str, subject: str, html_body: str, text_body: str = '') -> bool:
    """
    Send a transactional email via Amazon SES.
    Returns True on success, False on failure (caller should fall back to SMTP).
    SES_SENDER_EMAIL must be a verified address/domain in AWS SES console.
    """
    client = get_ses()
    if client is None or not SES_SENDER_EMAIL:
        logger.warning('SES not configured (missing AWS credentials or AWS_SES_SENDER_EMAIL). '
                       'Falling back to SMTP.')
        return False

    body: dict = {'Html': {'Charset': 'UTF-8', 'Data': html_body}}
    if text_body:
        body['Text'] = {'Charset': 'UTF-8', 'Data': text_body}

    try:
        client.send_email(
            Source=SES_SENDER_EMAIL,
            Destination={'ToAddresses': [to_email]},
            Message={
                'Subject': {'Charset': 'UTF-8', 'Data': subject},
                'Body': body,
            },
        )
        logger.info('SES email sent to %s | subject: %s', to_email, subject)
        return True
    except ClientError as exc:
        err_code = exc.response['Error']['Code']
        logger.error('SES send_email failed (%s) to %s: %s', err_code, to_email, exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Textract – Document Text Extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_document_fields(image_bytes: bytes) -> dict:
    """
    Extract key-value pairs and raw text from a document image using Amazon Textract.
    Designed for supplier certificates (GSTIN, FSSAI, business name, address).

    Returns:
        {
          'raw_text': str,           # All detected text joined
          'fields': {key: value},    # Key-value pairs from FORMS analysis
          'gstin': str | None,       # Detected GSTIN (15-char alphanumeric)
          'business_name': str | None,
          'fssai': str | None,       # 14-digit FSSAI number
        }
    """
    client = get_textract()
    if client is None:
        return {'raw_text': '', 'fields': {}, 'gstin': None, 'business_name': None, 'fssai': None}

    try:
        response = client.analyze_document(
            Document={'Bytes': image_bytes},
            FeatureTypes=['FORMS'],
        )
    except ClientError as exc:
        logger.exception('Textract analyze_document failed: %s', exc)
        return {'raw_text': '', 'fields': {}, 'gstin': None, 'business_name': None, 'fssai': None}

    # --- collect all blocks ---
    blocks      = response.get('Blocks', [])
    block_map   = {b['Id']: b for b in blocks}

    # Raw text from LINE blocks
    raw_lines = [b['Text'] for b in blocks if b['BlockType'] == 'LINE' and 'Text' in b]
    raw_text  = ' '.join(raw_lines)

    # Key-value pairs from FORM blocks
    fields: dict = {}
    for block in blocks:
        if block['BlockType'] != 'KEY_VALUE_SET':
            continue
        if 'KEY' not in block.get('EntityTypes', []):
            continue
        # Get key text
        key_text  = _get_text_from_relationships(block, block_map)
        # Find VALUE partner
        value_text = ''
        for rel in block.get('Relationships', []):
            if rel['Type'] == 'VALUE':
                for vid in rel['Ids']:
                    value_block = block_map.get(vid, {})
                    value_text  = _get_text_from_relationships(value_block, block_map)
        if key_text:
            fields[key_text.strip()] = value_text.strip()

    # --- extract specific identifiers using regex ---
    gstin         = _extract_pattern(raw_text, r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b')
    fssai         = _extract_pattern(raw_text, r'\b\d{14}\b')
    business_name = _extract_business_name(fields, raw_lines)

    return {
        'raw_text':      raw_text,
        'fields':        fields,
        'gstin':         gstin,
        'business_name': business_name,
        'fssai':         fssai,
    }


def _get_text_from_relationships(block: dict, block_map: dict) -> str:
    text = ''
    for rel in block.get('Relationships', []):
        if rel['Type'] == 'CHILD':
            for cid in rel['Ids']:
                child = block_map.get(cid, {})
                if child.get('BlockType') == 'WORD':
                    text += child.get('Text', '') + ' '
    return text.strip()


def _extract_pattern(text: str, pattern: str) -> Optional[str]:
    m = re.search(pattern, text)
    return m.group(0) if m else None


def _extract_business_name(fields: dict, raw_lines: list) -> Optional[str]:
    name_keys = {'business name', 'firm name', 'trade name', 'company name', 'name of business', 'legal name'}
    for k, v in fields.items():
        if k.lower() in name_keys and v:
            return v
    # Fallback: first capitalised line longer than 5 chars
    for line in raw_lines[:5]:
        if len(line) > 5 and line[0].isupper():
            return line
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Rekognition – Product Image Auto-Tagging
# ─────────────────────────────────────────────────────────────────────────────

# Map Rekognition labels → product categories used in VendorConnect
_LABEL_TO_CATEGORY: dict = {
    'vegetable': 'vegetables', 'carrot': 'vegetables', 'potato': 'vegetables',
    'tomato': 'vegetables', 'onion': 'vegetables', 'cabbage': 'vegetables',
    'spinach': 'vegetables', 'broccoli': 'vegetables', 'cucumber': 'vegetables',
    'fruit': 'fruits', 'apple': 'fruits', 'mango': 'fruits', 'banana': 'fruits',
    'orange': 'fruits', 'grape': 'fruits', 'watermelon': 'fruits',
    'grain': 'grains', 'rice': 'grains', 'wheat': 'grains', 'corn': 'grains',
    'flour': 'grains', 'bread': 'grains',
    'spice': 'spices', 'herb': 'spices', 'pepper': 'spices', 'turmeric': 'spices',
    'coriander': 'spices', 'cumin': 'spices',
    'oil': 'oils', 'ghee': 'oils', 'butter': 'oils',
    'dairy': 'dairy', 'milk': 'dairy', 'cheese': 'dairy', 'yogurt': 'dairy',
    'meat': 'meat', 'chicken': 'meat', 'fish': 'seafood', 'seafood': 'seafood',
    'egg': 'dairy', 'nut': 'dry_fruits', 'almond': 'dry_fruits', 'cashew': 'dry_fruits',
    'packaging': 'packaging', 'box': 'packaging', 'container': 'packaging', 'bag': 'packaging',
    'beverage': 'beverages', 'drink': 'beverages', 'water': 'beverages', 'juice': 'beverages',
}


def auto_tag_product_image(image_bytes: bytes) -> dict:
    """
    Use Rekognition to suggest a product name and category from an image.
    Returns:
        {
          'suggested_name': str,       # Best label as product name
          'suggested_category': str,   # Mapped VendorConnect category
          'labels': [str],             # All detected labels (confidence >= 75)
          'confidence': float,         # Confidence of top label
        }
    """
    client = get_rekognition()
    if client is None:
        return {'suggested_name': '', 'suggested_category': 'other', 'labels': [], 'confidence': 0}

    try:
        response = client.detect_labels(
            Image={'Bytes': image_bytes},
            MaxLabels=15,
            MinConfidence=75,
        )
    except ClientError as exc:
        logger.exception('Rekognition auto-tag failed: %s', exc)
        return {'suggested_name': '', 'suggested_category': 'other', 'labels': [], 'confidence': 0}

    labels = response.get('Labels', [])
    if not labels:
        return {'suggested_name': '', 'suggested_category': 'other', 'labels': [], 'confidence': 0}

    label_names   = [lbl['Name'] for lbl in labels]
    top_label     = labels[0]
    top_name      = top_label['Name']
    top_confidence = round(top_label['Confidence'], 1)

    # Determine category
    suggested_category = 'other'
    for lbl in label_names:
        key = lbl.lower()
        if key in _LABEL_TO_CATEGORY:
            suggested_category = _LABEL_TO_CATEGORY[key]
            break
        # partial match
        for pattern, cat in _LABEL_TO_CATEGORY.items():
            if pattern in key:
                suggested_category = cat
                break
        if suggested_category != 'other':
            break

    return {
        'suggested_name':     top_name,
        'suggested_category': suggested_category,
        'labels':             label_names,
        'confidence':         top_confidence,
    }


# ─────────────────────────────────────────────────────────────────────────────
# DynamoDB – Real-time Chat & Live Notifications
# ─────────────────────────────────────────────────────────────────────────────

CHAT_TABLE        = os.environ.get('DYNAMO_CHAT_TABLE',         'vendorconnect_chat')
NOTIF_TABLE       = os.environ.get('DYNAMO_NOTIF_TABLE',        'vendorconnect_notifications')

def _ensure_chat_tables():
    """Create DynamoDB tables if they don't already exist (dev convenience)."""
    client = get_dynamodb()
    if client is None:
        return
    existing = []
    try:
        existing = [t['TableName'] for t in client.list_tables().get('TableNames', [])]
    except Exception:
        pass

    if CHAT_TABLE not in existing:
        try:
            client.create_table(
                TableName=CHAT_TABLE,
                AttributeDefinitions=[
                    {'AttributeName': 'room_id',    'AttributeType': 'S'},
                    {'AttributeName': 'timestamp',  'AttributeType': 'S'},
                ],
                KeySchema=[
                    {'AttributeName': 'room_id',   'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp',  'KeyType': 'RANGE'},
                ],
                BillingMode='PAY_PER_REQUEST',
            )
            logger.info('DynamoDB: created table %s', CHAT_TABLE)
        except Exception as exc:
            logger.warning('Could not create chat table: %s', exc)

    if NOTIF_TABLE not in existing:
        try:
            client.create_table(
                TableName=NOTIF_TABLE,
                AttributeDefinitions=[
                    {'AttributeName': 'user_id',    'AttributeType': 'S'},
                    {'AttributeName': 'timestamp',  'AttributeType': 'S'},
                ],
                KeySchema=[
                    {'AttributeName': 'user_id',   'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp',  'KeyType': 'RANGE'},
                ],
                BillingMode='PAY_PER_REQUEST',
            )
            logger.info('DynamoDB: created table %s', NOTIF_TABLE)
        except Exception as exc:
            logger.warning('Could not create notifications table: %s', exc)


def save_chat_message(room_id: str, sender_id: str, sender_name: str,
                       message: str, msg_type: str = 'text') -> dict:
    """
    Save a chat message to DynamoDB.
    room_id format: 'vendor_{vendor_id}_customer_{customer_id}'
    Returns the saved message dict or empty dict on failure.
    """
    res = get_dynamodb_resource()
    if res is None:
        # graceful local fallback — store nothing, return the message
        logger.warning('DynamoDB unavailable – chat message not persisted.')
        return {}
    try:
        table = res.Table(CHAT_TABLE)
        ts = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())
        msg_id = str(uuid.uuid4())
        item = {
            'room_id':     room_id,
            'timestamp':   ts,
            'msg_id':      msg_id,
            'sender_id':   str(sender_id),
            'sender_name': sender_name,
            'message':     message,
            'msg_type':    msg_type,
            'read':        False,
        }
        table.put_item(Item=item)
        return item
    except Exception as exc:
        logger.warning('DynamoDB save_chat_message unavailable (%s) – using local fallback.', type(exc).__name__)
        return {}


def get_chat_messages(room_id: str, limit: int = 50) -> list:
    """
    Fetch the last `limit` messages for a chat room.
    Returns list of message dicts, newest last.
    """
    res = get_dynamodb_resource()
    if res is None:
        return []
    try:
        from boto3.dynamodb.conditions import Key
        table = res.Table(CHAT_TABLE)
        resp = table.query(
            KeyConditionExpression=Key('room_id').eq(room_id),
            ScanIndexForward=False,
            Limit=limit,
        )
        messages = resp.get('Items', [])
        return list(reversed(messages))
    except Exception as exc:
        logger.warning('DynamoDB get_chat_messages unavailable (%s) – using local fallback.', type(exc).__name__)
        return []


def save_notification(user_id: str, title: str, body: str,
                       notif_type: str = 'info', link: str = '') -> dict:
    """
    Save a live notification for a user in DynamoDB.
    Returns the saved item or empty dict on failure.
    """
    res = get_dynamodb_resource()
    if res is None:
        logger.warning('DynamoDB unavailable – notification not persisted.')
        return {}
    try:
        table = res.Table(NOTIF_TABLE)
        ts = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())
        item = {
            'user_id':    str(user_id),
            'timestamp':  ts,
            'notif_id':   str(uuid.uuid4()),
            'title':      title,
            'body':       body,
            'type':       notif_type,
            'link':       link,
            'read':       False,
        }
        table.put_item(Item=item)
        return item
    except Exception as exc:
        logger.warning('DynamoDB save_notification unavailable (%s) – using local fallback.', type(exc).__name__)
        return {}


def get_notifications(user_id: str, unread_only: bool = False, limit: int = 20) -> list:
    """
    Fetch notifications for a user. Returns newest first.
    """
    res = get_dynamodb_resource()
    if res is None:
        return []
    try:
        from boto3.dynamodb.conditions import Key, Attr
        table = res.Table(NOTIF_TABLE)
        kwargs = dict(
            KeyConditionExpression=Key('user_id').eq(str(user_id)),
            ScanIndexForward=False,
            Limit=limit,
        )
        if unread_only:
            kwargs['FilterExpression'] = Attr('read').eq(False)
        resp = table.query(**kwargs)
        return resp.get('Items', [])
    except Exception as exc:
        logger.warning('DynamoDB get_notifications unavailable (%s) – using local fallback.', type(exc).__name__)
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Lambda + EventBridge – Auto-expire orders & Scheduled jobs
# ─────────────────────────────────────────────────────────────────────────────

LAMBDA_ORDER_EXPIRY_FN  = os.environ.get('LAMBDA_ORDER_EXPIRY_FN',  'vendorconnect-order-expiry')
LAMBDA_REPORT_FN        = os.environ.get('LAMBDA_REPORT_FN',        'vendorconnect-daily-report')
EVENTBRIDGE_BUS         = os.environ.get('EVENTBRIDGE_BUS',         'vendorconnect-events')


def invoke_lambda(function_name: str, payload: dict, invocation_type: str = 'Event') -> dict:
    """
    Invoke an AWS Lambda function.
    invocation_type: 'Event' (async) or 'RequestResponse' (sync).
    Returns response dict or empty dict on failure.
    """
    client = get_lambda()
    if client is None:
        logger.warning('Lambda unavailable – skipping invoke of %s', function_name)
        return {}
    try:
        resp = client.invoke(
            FunctionName=function_name,
            InvocationType=invocation_type,
            Payload=json.dumps(payload).encode(),
        )
        status = resp.get('StatusCode', 0)
        logger.info('Lambda invoke %s → HTTP %s', function_name, status)
        if invocation_type == 'RequestResponse':
            raw = resp.get('Payload', b'{}')
            if hasattr(raw, 'read'):
                raw = raw.read()
            return json.loads(raw or '{}')
        return {'status': status}
    except Exception as exc:
        logger.exception('Lambda invoke failed (%s): %s', function_name, exc)
        return {}


def schedule_order_expiry(order_id: int, group_order_id: int, expire_at_iso: str) -> bool:
    """
    Put an EventBridge event to auto-expire a group order at a scheduled time.
    Returns True on success.
    """
    client = get_events()
    if client is None:
        logger.warning('EventBridge unavailable – order expiry not scheduled.')
        return False
    try:
        event = {
            'order_id':       order_id,
            'group_order_id': group_order_id,
            'expire_at':      expire_at_iso,
            'action':         'EXPIRE_ORDER',
        }
        resp = client.put_events(
            Entries=[{
                'Source':       'com.vendorconnect.orders',
                'DetailType':   'OrderExpiry',
                'Detail':       json.dumps(event),
                'EventBusName': EVENTBRIDGE_BUS,
            }]
        )
        failed = resp.get('FailedEntryCount', 0)
        if failed:
            logger.warning('EventBridge: %d entries failed', failed)
            return False
        logger.info('EventBridge: scheduled expiry for order %s', order_id)
        return True
    except Exception as exc:
        logger.exception('EventBridge schedule_order_expiry failed: %s', exc)
        return False


def trigger_scheduled_report(vendor_id: int, report_type: str = 'daily_summary') -> bool:
    """
    Fire an EventBridge event to trigger a scheduled analytics report via Lambda.
    """
    client = get_events()
    if client is None:
        return False
    try:
        event = {
            'vendor_id':   vendor_id,
            'report_type': report_type,
            'triggered_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        }
        resp = client.put_events(
            Entries=[{
                'Source':       'com.vendorconnect.reports',
                'DetailType':   'ScheduledReport',
                'Detail':       json.dumps(event),
                'EventBusName': EVENTBRIDGE_BUS,
            }]
        )
        failed = resp.get('FailedEntryCount', 0)
        logger.info('EventBridge: report trigger for vendor %s, failed=%s', vendor_id, failed)
        return failed == 0
    except Exception as exc:
        logger.exception('EventBridge trigger_scheduled_report failed: %s', exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Location Service – Route Optimisation & Delivery Geofencing
# ─────────────────────────────────────────────────────────────────────────────

LOCATION_ROUTE_CALCULATOR = os.environ.get('LOCATION_ROUTE_CALC', 'vendorconnect-route-calc')
LOCATION_GEOFENCE_COLL    = os.environ.get('LOCATION_GEOFENCE_COLL', 'vendorconnect-geofences')
LOCATION_TRACKER          = os.environ.get('LOCATION_TRACKER', 'vendorconnect-tracker')


def calculate_route(origin_lat: float, origin_lng: float,
                    dest_lat: float, dest_lng: float) -> dict:
    """
    Calculate the optimised delivery route between two coordinates.
    Returns dict with distance_km, duration_minutes, legs and a
    simplified polyline (list of [lat, lng] pairs).
    Falls back to straight-line estimate when Location Service unavailable.
    """
    client = get_location()
    if client is None:
        # Haversine straight-line fallback
        import math
        R = 6371
        dlat = math.radians(dest_lat - origin_lat)
        dlng = math.radians(dest_lng - origin_lng)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(origin_lat)) * \
            math.cos(math.radians(dest_lat)) * math.sin(dlng/2)**2
        dist_km = round(2 * R * math.asin(math.sqrt(a)), 2)
        return {
            'distance_km':       dist_km,
            'duration_minutes':  round(dist_km * 3, 1),   # ~20 km/h estimate
            'polyline':          [[origin_lat, origin_lng], [dest_lat, dest_lng]],
            'source':            'fallback',
        }
    try:
        resp = client.calculate_route(
            CalculatorName=LOCATION_ROUTE_CALCULATOR,
            DeparturePosition=[origin_lng, origin_lat],   # [lng, lat]
            DestinationPosition=[dest_lng, dest_lat],
            TravelMode='Truck',
            DistanceUnit='Kilometers',
        )
        summary = resp['Summary']
        legs = resp.get('Legs', [])
        polyline = []
        for leg in legs:
            for step in leg.get('Steps', []):
                pos = step.get('StartPosition', [])
                if len(pos) == 2:
                    polyline.append([pos[1], pos[0]])   # [lat, lng]
        return {
            'distance_km':      round(summary.get('Distance', 0), 2),
            'duration_minutes': round(summary.get('DurationSeconds', 0) / 60, 1),
            'polyline':         polyline,
            'source':           'aws_location',
        }
    except Exception as exc:
        logger.warning('Location calculate_route unavailable (%s) – using haversine fallback.', type(exc).__name__)
        import math
        R = 6371
        dlat = math.radians(dest_lat - origin_lat)
        dlng = math.radians(dest_lng - origin_lng)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(origin_lat)) * \
            math.cos(math.radians(dest_lat)) * math.sin(dlng/2)**2
        dist_km = round(2 * R * math.asin(math.sqrt(a)), 2)
        return {
            'distance_km':       dist_km,
            'duration_minutes':  round(dist_km * 3, 1),
            'polyline':          [[origin_lat, origin_lng], [dest_lat, dest_lng]],
            'source':            'fallback',
        }


def create_geofence(geofence_id: str, center_lat: float, center_lng: float,
                     radius_meters: float = 500) -> bool:
    """
    Create a circular geofence around a delivery zone (e.g. vendor's shop).
    Returns True on success.
    """
    client = get_location()
    if client is None:
        logger.warning('Location Service unavailable – geofence not created.')
        return False
    try:
        client.put_geofence(
            CollectionName=LOCATION_GEOFENCE_COLL,
            GeofenceId=geofence_id,
            Geometry={
                'Circle': {
                    'Center': [center_lng, center_lat],
                    'Radius': radius_meters,
                }
            },
        )
        logger.info('Geofence created: %s (r=%.0fm)', geofence_id, radius_meters)
        return True
    except Exception as exc:
        logger.exception('Location create_geofence failed: %s', exc)
        return False


def check_geofence(geofence_id: str, lat: float, lng: float) -> dict:
    """
    Check whether a point (lat/lng) is inside the named geofence.
    Returns {'inside': bool, 'geofence_id': str}.
    """
    client = get_location()
    if client is None:
        return {'inside': False, 'geofence_id': geofence_id, 'source': 'unavailable'}
    try:
        resp = client.get_geofence(
            CollectionName=LOCATION_GEOFENCE_COLL,
            GeofenceId=geofence_id,
        )
        geometry = resp.get('Geometry', {}).get('Circle', {})
        center = geometry.get('Center', [0, 0])    # [lng, lat]
        radius = geometry.get('Radius', 0)
        import math
        R = 6371000
        dlat = math.radians(lat - center[1])
        dlng = math.radians(lng - center[0])
        a = math.sin(dlat/2)**2 + math.cos(math.radians(center[1])) * \
            math.cos(math.radians(lat)) * math.sin(dlng/2)**2
        dist_m = 2 * R * math.asin(math.sqrt(a))
        return {
            'inside':      dist_m <= radius,
            'distance_m':  round(dist_m, 1),
            'geofence_id': geofence_id,
            'source':      'aws_location',
        }
    except Exception as exc:
        logger.exception('Location check_geofence failed: %s', exc)
        return {'inside': False, 'geofence_id': geofence_id, 'source': 'error'}


def update_device_position(device_id: str, lat: float, lng: float) -> bool:
    """
    Update the live position of a delivery agent tracker device.
    """
    client = get_location()
    if client is None:
        return False
    try:
        client.batch_update_device_position(
            TrackerName=LOCATION_TRACKER,
            Updates=[{
                'DeviceId':  str(device_id),
                'Position':  [lng, lat],
                'SampleTime': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            }]
        )
        return True
    except Exception as exc:
        logger.warning('Location update_device_position unavailable (%s) – skipping.', type(exc).__name__)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Personalize – ML Product Recommendations
# ─────────────────────────────────────────────────────────────────────────────

PERSONALIZE_CAMPAIGN_ARN = os.environ.get('PERSONALIZE_CAMPAIGN_ARN', '')


def get_recommendations(user_id: str, num_results: int = 6) -> list:
    """
    Fetch personalised product recommendations for a user from AWS Personalize.
    Returns list of {'item_id': str, 'score': float} dicts.
    Falls back to empty list if Personalize is not configured.
    """
    if not PERSONALIZE_CAMPAIGN_ARN:
        logger.info('Personalize: PERSONALIZE_CAMPAIGN_ARN not set – returning empty list.')
        return []
    client = get_personalize_runtime()
    if client is None:
        return []
    try:
        resp = client.get_recommendations(
            campaignArn=PERSONALIZE_CAMPAIGN_ARN,
            userId=str(user_id),
            numResults=num_results,
        )
        return [
            {'item_id': r['itemId'], 'score': round(r.get('score', 0), 4)}
            for r in resp.get('itemList', [])
        ]
    except Exception as exc:
        logger.exception('Personalize get_recommendations failed: %s', exc)
        return []


def record_user_event(user_id: str, item_id: str, event_type: str = 'click',
                       session_id: str = '') -> bool:
    """
    Record a user interaction event (view/click/purchase) to improve
    future Personalize recommendations.
    """
    if not PERSONALIZE_CAMPAIGN_ARN:
        return False
    client = get_personalize_runtime()
    if client is None:
        return False
    # Derive the event tracker ARN from campaign ARN (same account/region prefix)
    event_tracker_arn = os.environ.get('PERSONALIZE_EVENT_TRACKER_ARN', '')
    if not event_tracker_arn:
        return False
    try:
        import boto3 as _boto3
        events_client = _boto3.client(
            'personalize-events',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_KEY,
        )
        events_client.put_events(
            trackingId=event_tracker_arn,
            userId=str(user_id),
            sessionId=session_id or str(uuid.uuid4()),
            eventList=[{
                'eventType':   event_type,
                'itemId':      str(item_id),
                'sentAt':      time.time(),
            }],
        )
        return True
    except Exception as exc:
        logger.exception('Personalize record_user_event failed: %s', exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Cognito – Managed Authentication with MFA
# ─────────────────────────────────────────────────────────────────────────────

COGNITO_USER_POOL_ID  = os.environ.get('COGNITO_USER_POOL_ID',  '')
COGNITO_APP_CLIENT_ID = os.environ.get('COGNITO_APP_CLIENT_ID', '')


def cognito_register(email: str, password: str, name: str, phone: str = '') -> dict:
    """
    Register a new user in the Cognito User Pool.
    Returns {'success': bool, 'user_sub': str, 'message': str}.
    """
    if not COGNITO_USER_POOL_ID or not COGNITO_APP_CLIENT_ID:
        return {'success': False, 'user_sub': '', 'message': 'Cognito not configured'}
    client = get_cognito()
    if client is None:
        return {'success': False, 'user_sub': '', 'message': 'Cognito client unavailable'}
    try:
        attrs = [
            {'Name': 'email', 'Value': email},
            {'Name': 'name',  'Value': name},
        ]
        if phone:
            attrs.append({'Name': 'phone_number', 'Value': phone})
        resp = client.sign_up(
            ClientId=COGNITO_APP_CLIENT_ID,
            Username=email,
            Password=password,
            UserAttributes=attrs,
        )
        return {
            'success':  True,
            'user_sub': resp.get('UserSub', ''),
            'message':  'Registration successful. Check email for verification code.',
        }
    except client.exceptions.UsernameExistsException:
        return {'success': False, 'user_sub': '', 'message': 'Email already registered in Cognito.'}
    except Exception as exc:
        logger.exception('Cognito register failed: %s', exc)
        return {'success': False, 'user_sub': '', 'message': str(exc)}


def cognito_login(email: str, password: str) -> dict:
    """
    Authenticate a user via Cognito.
    Returns {'success': bool, 'tokens': dict, 'challenge': str, 'session': str, 'message': str}.
    challenge is non-empty when MFA is required ('SMS_MFA' | 'SOFTWARE_TOKEN_MFA').
    """
    if not COGNITO_USER_POOL_ID or not COGNITO_APP_CLIENT_ID:
        return {'success': False, 'tokens': {}, 'challenge': '', 'session': '', 'message': 'Cognito not configured'}
    client = get_cognito()
    if client is None:
        return {'success': False, 'tokens': {}, 'challenge': '', 'session': '', 'message': 'Cognito unavailable'}
    try:
        resp = client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={'USERNAME': email, 'PASSWORD': password},
            ClientId=COGNITO_APP_CLIENT_ID,
        )
        challenge = resp.get('ChallengeName', '')
        if challenge in ('SMS_MFA', 'SOFTWARE_TOKEN_MFA'):
            return {
                'success':   False,
                'tokens':    {},
                'challenge': challenge,
                'session':   resp.get('Session', ''),
                'message':   'MFA code required',
            }
        auth_result = resp.get('AuthenticationResult', {})
        return {
            'success':   True,
            'tokens': {
                'access_token':  auth_result.get('AccessToken', ''),
                'id_token':      auth_result.get('IdToken', ''),
                'refresh_token': auth_result.get('RefreshToken', ''),
            },
            'challenge': '',
            'session':   '',
            'message':   'Login successful',
        }
    except Exception as exc:
        logger.exception('Cognito login failed: %s', exc)
        return {'success': False, 'tokens': {}, 'challenge': '', 'session': '', 'message': str(exc)}


def cognito_verify_mfa(email: str, mfa_code: str, session: str,
                        challenge: str = 'SMS_MFA') -> dict:
    """
    Complete MFA challenge after cognito_login returns a challenge.
    Returns {'success': bool, 'tokens': dict, 'message': str}.
    """
    if not COGNITO_APP_CLIENT_ID:
        return {'success': False, 'tokens': {}, 'message': 'Cognito not configured'}
    client = get_cognito()
    if client is None:
        return {'success': False, 'tokens': {}, 'message': 'Cognito unavailable'}
    code_key = 'SMS_MFA_CODE' if challenge == 'SMS_MFA' else 'SOFTWARE_TOKEN_MFA_CODE'
    try:
        resp = client.respond_to_auth_challenge(
            ClientId=COGNITO_APP_CLIENT_ID,
            ChallengeName=challenge,
            Session=session,
            ChallengeResponses={
                'USERNAME': email,
                code_key:   mfa_code,
            },
        )
        auth_result = resp.get('AuthenticationResult', {})
        return {
            'success': True,
            'tokens': {
                'access_token':  auth_result.get('AccessToken', ''),
                'id_token':      auth_result.get('IdToken', ''),
                'refresh_token': auth_result.get('RefreshToken', ''),
            },
            'message': 'MFA verified successfully',
        }
    except Exception as exc:
        logger.exception('Cognito verify_mfa failed: %s', exc)
        return {'success': False, 'tokens': {}, 'message': str(exc)}


def cognito_confirm_registration(email: str, code: str) -> dict:
    """Confirm a new user registration with the emailed verification code."""
    if not COGNITO_APP_CLIENT_ID:
        return {'success': False, 'message': 'Cognito not configured'}
    client = get_cognito()
    if client is None:
        return {'success': False, 'message': 'Cognito unavailable'}
    try:
        client.confirm_sign_up(
            ClientId=COGNITO_APP_CLIENT_ID,
            Username=email,
            ConfirmationCode=code,
        )
        return {'success': True, 'message': 'Account verified successfully'}
    except Exception as exc:
        logger.exception('Cognito confirm_registration failed: %s', exc)
        return {'success': False, 'message': str(exc)}
