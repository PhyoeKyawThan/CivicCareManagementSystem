from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IssueViewSet, IssueTypeViewSet, IssueAttachmentViewSet, VoteViewSet

router = DefaultRouter()
router.register(r'issues', IssueViewSet)
router.register(r'issue_types', IssueTypeViewSet)
router.register(r'attachments', IssueAttachmentViewSet)
router.register(r'votes', VoteViewSet)

urlpatterns = [
    path('', include(router.urls)),
]