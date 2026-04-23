from rest_framework.decorators import api_view
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.parsers import FormParser, MultiPartParser
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from rest_framework.parsers import JSONParser

from wrappers.meta_whatsapp import send_whatsapp_message

from bigboy.accounts.models import Account, State
from bigboy.chats.api.v1.serializers import WhatsAppMessageSerializer
from bigboy.chats.commands.registry import COMMAND_REGISTRY
from bigboy.chats.handlers.quiz import QuizHandler
from bigboy.chats.handlers.lesson import LessonHandler
from bigboy.chats.handlers.generation import GenerationHandler


# class WhatsAppWebhook(generics.GenericAPIView):
#     serializer_class = WhatsAppMessageSerializer
#     parser_classes    = [FormParser, MultiPartParser]   
#     permission_classes = [permissions.AllowAny]        

#     def post(self, request: Request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         body = serializer.validated_data["Body"].strip()
#         user_phone = serializer.validated_data.get("From") 
#         user_phone = user_phone.split(":")[1]

#         try:
#             account = Account.objects.get(phone_number=user_phone)
#         except Account.DoesNotExist:
#             # account = Account.objects.create(phone_number=user_phone, state=State.INITIAL)
#             # account.save()
#             send_whatsapp_message(user_phone, "Welcome to ClassmateBot! Type /help for available commands.")
#             return Response({"status": "account created"}, status=status.HTTP_201_CREATED)
        
#         state = State.objects.get(account=account)
#         if state.state == State.Mode.IN_QUIZ:
#             quiz_handler = QuizHandler(state, body)
#             response_message = quiz_handler.handle()
#             if response_message:
#                 send_whatsapp_message(user_phone, response_message)
#             return Response({"status": "quiz response handled"}, status=status.HTTP_200_OK)
#         elif state.state == State.Mode.IN_LESSON:
#             lesson_handler = LessonHandler(state, body)
#             response_message = lesson_handler.handle()
#             if response_message:
#                 send_whatsapp_message(user_phone, response_message)    
#             return Response({"status": "lesson response handled"}, status=status.HTTP_200_OK)   

#         elif state.state == State.Mode.IN_GENERATION:
#             generation_handler = GenerationHandler(state, body)
#             response_message = generation_handler.handle()
#             if response_message:
#                 send_whatsapp_message(user_phone, response_message)
#             return Response({"status": "generation response handled"}, status=status.HTTP_200_OK)         
        
#         command = body.lower().split(" ")[0]

#         if command not in COMMAND_REGISTRY.keys():
#             send_whatsapp_message(user_phone, "Unknown command. Please type /help for available commands.")
#             return Response({"status": "unknown command"}, status=status.HTTP_400_BAD_REQUEST)
        
#         command_config = COMMAND_REGISTRY[command]
#         command_class = command_config["class"]
#         additional_args = command_config.get("additional_args", [])
#         error_message = command_config["error_message"]
        
#         if additional_args:
#             body_parts = body.split(" ")
#             if len(body_parts) > len(additional_args):
#                 kwargs = {arg: body_parts[i + 1] for i, arg in enumerate(additional_args)}
#                 command_instance = command_class(to_number=user_phone, **kwargs)
#             else:
#                 send_whatsapp_message(user_phone, error_message)
#                 return Response({"status": "error"}, status=status.HTTP_400_BAD_REQUEST)
#         else:
#             command_instance = command_class(to_number=user_phone)

#         response_message = command_instance.execute()
#         if response_message:
#             send_whatsapp_message(user_phone, response_message)    
        
#         return Response({"status": "help message sent"})



class WhatsAppWebhook(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser]

    def get(self, request):
        """
        Required for Meta Webhook Verification.
        """
        mode = request.query_params.get('hub.mode')
        token = request.query_params.get('hub.verify_token')
        challenge = request.query_params.get('hub.challenge')

        if mode == 'subscribe' and token == settings.META_VERIFY_TOKEN:
            return Response(int(challenge), status=status.HTTP_200_OK)
        return Response("Forbidden", status=status.HTTP_403_FORBIDDEN)

    def post(self, request):
        data = request.data
        
        # Meta sends status updates (delivered, read) in the same webhook.
        # We only care about actual messages.
        try:
            entry = data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            
            if 'messages' not in value:
                return Response({"status": "ignored"}, status=status.HTTP_200_OK)

            message = value['messages'][0]
            print(f"Received message: {message}")
            user_phone = message['from'] # Format: 23480...
            body = message.get('text', {}).get('body', "").strip()

            # Logic to find/create account (Matching your existing logic)
            try:
                account = Account.objects.get(phone_number=f"+{user_phone}")
            except Account.DoesNotExist:
                account = Account.objects.create_user(phone_number=f"+{user_phone}")
                account.save()
                State.objects.create(account=account)
                send_whatsapp_message(f"+{user_phone}", "Welcome to ClassmateBot! Type /help to start.")
                return Response({"status": "new user"}, status=status.HTTP_200_OK)
            

            ##############
            state = State.objects.get(account=account)
            if state.state == State.Mode.IN_QUIZ:
                quiz_handler = QuizHandler(state, body)
                response_message = quiz_handler.handle()
                if response_message:
                    send_whatsapp_message(f"+{user_phone}", response_message)
                return Response({"status": "quiz response handled"}, status=status.HTTP_200_OK)
            elif state.state == State.Mode.IN_LESSON:
                lesson_handler = LessonHandler(state, body)
                response_message = lesson_handler.handle()
                if response_message:
                    send_whatsapp_message(f"+{user_phone}", response_message)    
                return Response({"status": "lesson response handled"}, status=status.HTTP_200_OK)   

            elif state.state == State.Mode.IN_GENERATION:
                generation_handler = GenerationHandler(state, body)
                response_message = generation_handler.handle()
                if response_message:
                    send_whatsapp_message(f"+{user_phone}", response_message)
                return Response({"status": "generation response handled"}, status=status.HTTP_200_OK)         
            
            command = body.lower().split(" ")[0]

            if command not in COMMAND_REGISTRY.keys():
                send_whatsapp_message(f"+{user_phone}", "Unknown command. Please type /help for available commands.")
                return Response({"status": "unknown command"}, status=status.HTTP_400_BAD_REQUEST)
            
            command_config = COMMAND_REGISTRY[command]
            command_class = command_config["class"]
            additional_args = command_config.get("additional_args", [])
            error_message = command_config["error_message"]
            
            if additional_args:
                body_parts = body.split(" ")
                if len(body_parts) > len(additional_args):
                    kwargs = {arg: body_parts[i + 1] for i, arg in enumerate(additional_args)}
                    command_instance = command_class(to_number=user_phone, **kwargs)
                else:
                    send_whatsapp_message(f"+{user_phone}", error_message)
                    return Response({"status": "error"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                command_instance = command_class(to_number=f"+{user_phone}")

            response_message = command_instance.execute()
            if response_message:
                send_whatsapp_message(f"+{user_phone}", response_message)    

            return Response({"status": "success"}, status=status.HTTP_200_OK)

        except (IndexError, KeyError) as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)