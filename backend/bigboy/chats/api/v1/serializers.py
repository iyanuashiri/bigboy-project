from rest_framework import serializers


class WhatsAppMessageSerializer(serializers.Serializer):
    """
    Minimal fields Twilio sends in its webhook.
    Add more if you need them (MessageSid, etc.).
    """
    Body = serializers.CharField()
    From = serializers.CharField(required=False, allow_blank=True)