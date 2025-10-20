from django.urls import path

from . import views

app_name = "chat"
urlpatterns = [
    path("chat/<int:thread_id>/", views.chat_room, name="chat_room"),
    path("chat/<int:thread_id>/create_order/", views.create_order_from_chat, name="create_order_from_chat"),
    path("chat/<int:thread_id>/send/", views.send_message, name="send_message"),
    path("chat/<int:thread_id>/messages/", views.get_messages, name="get_messages"),
    path("threads/", views.thread_list, name="thread_list"),
    path("contact-admin/", views.contact_admin, name="contact_admin"),
    path("send-component-list/<int:thread_id>/", views.send_component_list, name="send_component_list"),
]
