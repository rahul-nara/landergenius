# from rest_framework import serializers, viewsets
# from .models import BlogPage
# from wagtail.models import Page

# # Serializer for BlogPage
# class BlogPageSerializer(serializers.ModelSerializer):
#     """Serializer to convert BlogPage model data into JSON format"""

#     main_image_url = serializers.SerializerMethodField()

#     class Meta:
#         model = BlogPage
#         fields = ['id', 'title', 'date', 'intro', 'body', 'main_image_url']

#     def get_main_image_url(self, obj):
#         """Get the URL of the first image in the gallery"""
#         if obj.main_image():
#             return obj.main_image().get_rendition('fill-800x450').url
#         return None

# # API Viewset for BlogPage
# class BlogPageViewSet(viewsets.ModelViewSet):
#     """API endpoint to retrieve all published blog posts"""
#     queryset = BlogPage.objects.live().order_by('-first_published_at')
#     serializer_class = BlogPageSerializer
#     lookup_field = "id"  # Can be "slug" if needed

#     def perform_create(self, serializer):
#         """Set the parent page before saving the blog post"""
#         parent_page = Page.objects.get(slug="blog")
#         serializer.save(parent=parent_page)

from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.authentication import TokenAuthentication
from .models import BlogPage, BlogIndexPage

# ✅ Serializer for BlogPage
class BlogPageSerializer(serializers.ModelSerializer):
    main_image_url = serializers.SerializerMethodField()

    class Meta:
        model = BlogPage
        fields = ["id", "title", "date", "intro", "body", "main_image_url"]

    def get_main_image_url(self, obj):
        """Returns the first image URL from the gallery if available"""
        if obj.main_image():
            return obj.main_image().get_rendition("fill-800x450").url
        return None

# ✅ API ViewSet
class BlogPageViewSet(viewsets.ModelViewSet):
    serializer_class = BlogPageSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """Ensure we only return published, public pages"""
        return BlogPage.objects.live().public().order_by("-first_published_at")

    def perform_create(self, serializer):
        """Create a new BlogPage, assign it under BlogIndexPage, and publish it"""
        try:
            # ✅ Get the first BlogIndexPage
            blog_index = BlogIndexPage.objects.first()
            if not blog_index:
                raise serializers.ValidationError({"error": "No BlogIndexPage found! Create one in Wagtail Admin."})

            # ✅ Extract validated data
            validated_data = serializer.validated_data

            # ✅ Create a new BlogPage instance but DO NOT save yet
            new_blog_page = BlogPage(
                title=validated_data["title"],
                intro=validated_data["intro"],
                body=validated_data["body"],
                date=validated_data["date"]
            )

            # ✅ Add the blog as a child (this auto-sets path & depth)
            blog_index.add_child(instance=new_blog_page)

            # ✅ Save as a draft first, then publish it
            new_blog_page.save_revision().publish()  # 🔥 This ensures the page is published!

            # ✅ Assign the instance back to serializer
            serializer.instance = new_blog_page

        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})