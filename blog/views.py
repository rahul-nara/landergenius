from rest_framework.permissions import IsAuthenticated

class YourPostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
