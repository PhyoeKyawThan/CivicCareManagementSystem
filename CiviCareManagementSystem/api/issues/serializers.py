from rest_framework import serializers
from users.models import User
from issues.models import Issue, IssueAttachment, IssueType, Vote
from api.users.serializers import UserProfileSerializer

class IssueTypeSerializer(serializers.ModelSerializer): 
    class Meta:
        model = IssueType
        fields = ['id', 'name', 'sample_form', 'created_at']

class IssueAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueAttachment
        fields = ['id', 'file', 'file_type', 'created_at'] 

class VoteSerializer(serializers.ModelSerializer): 
    user = serializers.StringRelatedField(read_only=True) 
    
    class Meta:
        model = Vote
        fields = ['id', 'user', 'upvote', 'downvote', 'created_at']  

class IssueSerializer(serializers.ModelSerializer):  
    user = UserProfileSerializer(read_only=True)
    issue_type_details = IssueTypeSerializer(source="issue_type", read_only=True)
    attachments = IssueAttachmentSerializer(many=True, read_only=True)
    votes = VoteSerializer(many=True, read_only=True)
    
    attachment_files = serializers.ListField(
        child=serializers.FileField(max_length=10000, allow_empty_file=False),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Issue
        fields = [
            'id', 'user', 'issue_type', 'issue_type_details', 
            'title', 'description', 'status', 'priority',
            'location_latitude', 'location_longitude',
            'created_at', 'updated_at', 'closed_at',
            'attachments', 'attachment_files', 'votes'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'closed_at']
        extra_kwargs = {
            'issue_type': {'write_only': True}  
        }
    
    def create(self, validated_data):
        validated_data.pop('user', None)
        attachment_files = validated_data.pop('attachment_files', [])
        request = self.context.get('request')
        user = request.user if request else None
        
        issue = Issue.objects.create(
            user=user,
            **validated_data
        )
        
        for file in attachment_files:
            file_type = file.content_type if hasattr(file, 'content_type') else None
            IssueAttachment.objects.create(
                issue=issue,
                file=file,
                file_type=file_type
            )
        return issue
    
    def update(self, instance, validated_data):
        attachment_files = validated_data.pop('attachment_files', [])
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        for file in attachment_files:
            file_type = file.content_type if hasattr(file, 'content_type') else None
            IssueAttachment.objects.create(
                issue=instance,
                file=file,
                file_type=file_type
            )
        
        return instance