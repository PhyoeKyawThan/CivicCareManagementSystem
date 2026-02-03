from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers
from django_filters.rest_framework import DjangoFilterBackend
from users.models import User
from issues.models import Issue, IssueAttachment, IssueType, Vote
from .serializers import IssueSerializer, IssueSlimSerializer,IssueAttachmentSerializer, IssueTypeSerializer, VoteSerializer

class IssueViewSet(viewsets.ModelViewSet):
    """
    API endpoint for issues that allows viewing, creating, updating, and deleting issues.
    """
    queryset = Issue.objects.all().order_by('-created_at')
    serializer_class = IssueSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'issue_type', 'user']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status']
    ordering = ['-created_at']  # Default ordering

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'vote']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            # permission_classes = [permissions.IsAuthenticatedOrReadOnly]
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    def get_serializer_class(self):
        if self.request.query_params.get('search'):
            return IssueSlimSerializer
        return IssueSerializer
    def get_queryset(self):
        """
        Optionally restricts the returned issues based on query parameters.
        """
        queryset = super().get_queryset()
        
        # Filter by user if requested
        user_id = self.request.query_params.get('user_id', None)
        search_title = self.request.query_params.get('search_title', None)
        if user_id is not None:
            queryset = queryset.filter(user__id=user_id)
        if search_title:
            queryset = queryset.filter(title__icontains=search_title)
        # Filter by location radius (example implementation)
        lat = self.request.query_params.get('lat', None)
        lng = self.request.query_params.get('lng', None)
        radius = self.request.query_params.get('radius', None)  # in kilometers
        
        if all([lat, lng, radius]):
            # Note: This is a simplified example. You'd want to use proper geospatial queries
            # Consider using GeoDjango or a specialized library for production use
            pass
        
        return queryset

    def perform_create(self, serializer):
        """
        Set the user to the current user when creating an issue.
        """
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """
        Custom update logic if needed.
        """
        serializer.save()

    @action(detail=True, methods=['post', 'get', 'delete'], permission_classes=[permissions.AllowAny])
    def vote(self, request, pk=None):
        """
        Vote on an issue (upvote or downvote).
        POST: Create or update a vote
        GET: Check if user has voted
        DELETE: Remove vote
        """
        issue = self.get_object()
        user = request.user
        
        if request.method == 'POST':
            value = request.data.get('value', 0)
            
            # Validate vote 
            if value not in [-1, 0, 1]:
                return Response({'error': 'Invalid vote value'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get or create vote
            vote, created = Vote.objects.get_or_create(
                user=user,
                issue=issue,
                defaults={'value': value}
            )
            
            if not created:
                if value == 0:
                    vote.delete()
                # Update existing vote
                else:
                    vote.value = value
                    vote.save()
            
            votes = Vote.objects.filter(issue=issue)
            up = votes.filter(value=1).count()
            down = votes.filter(value=-1).count()
            score = up - down
            
            my_vote = 0
            user_vote = votes.filter(user=user).first()
            if user_vote:
                my_vote = user_vote.value

            vote_summary = {
                "up": up,
                "down": down,
                "score": score,
                "my_vote": my_vote
            }
            return Response(vote_summary, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
        elif request.method == 'GET':
            try:
                vote = Vote.objects.get(user=user, issue=issue)
                serializer = VoteSerializer(vote)
                return Response(serializer.data)
            except Vote.DoesNotExist:
                return Response({'has_voted': False})
        
        elif request.method == 'DELETE':
            try:
                vote = Vote.objects.get(user=user, issue=issue)
                vote.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Vote.DoesNotExist:
                return Response(
                    {'error': 'No vote found'},
                    status=status.HTTP_404_NOT_FOUND
                )

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def close(self, request, pk=None):
        """
        Close an issue (admin or owner only).
        """
        issue = self.get_object()
        
        # Check if user is admin or issue owner
        if not (request.user.is_staff or issue.user == request.user):
            return Response(
                {'error': 'You do not have permission to close this issue'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        issue.status = 'closed'
        issue.save()
        serializer = self.get_serializer(issue)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def attachments(self, request, pk=None):
        """
        Get all attachments for an issue.
        """
        issue = self.get_object()
        attachments = issue.attachments.all()
        serializer = IssueAttachmentSerializer(attachments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def vote_summary(self, request, pk=None):
        """
        Get vote summary for an issue.
        """
        issue = self.get_object()
        upvotes = Vote.objects.filter(issue=issue, upvote=True).count()
        downvotes = Vote.objects.filter(issue=issue, downvote=True).count()
        
        return Response({
            'upvotes': upvotes,
            'downvotes': downvotes,
            'total': upvotes - downvotes
        })


class IssueTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for issue types (typically admin only).
    """
    queryset = IssueType.objects.all().order_by('name')
    serializer_class = IssueTypeSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


class IssueAttachmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for issue attachments.
    """
    queryset = IssueAttachment.objects.all().order_by('-created_at')
    serializer_class = IssueAttachmentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by issue if provided
        issue_id = self.request.query_params.get('issue_id', None)
        if issue_id is not None:
            queryset = queryset.filter(issue__id=issue_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Set the issue when creating an attachment.
        """
        issue_id = self.request.data.get('issue')
        if issue_id:
            try:
                issue = Issue.objects.get(id=issue_id)
                serializer.save(issue=issue)
            except Issue.DoesNotExist:
                raise serializers.ValidationError({'issue': 'Issue not found'})
        else:
            raise serializers.ValidationError({'issue': 'Issue ID is required'})


class VoteViewSet(viewsets.ModelViewSet):
    """
    API endpoint for votes.
    """
    queryset = Vote.objects.all().order_by('-created_at')
    serializer_class = VoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['issue', 'user', 'upvote', 'downvote']
    
    def get_queryset(self):
        """
        Users can only see their own votes unless they're staff.
        """
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset
    
    def perform_create(self, serializer):
        """
        Set the user to the current user when creating a vote.
        """
        serializer.save(user=self.request.user)