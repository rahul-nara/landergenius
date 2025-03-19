from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.authentication import TokenAuthentication
from wagtail.images.models import Image
from django.core.files.base import ContentFile
import requests
from .models import BlogPage, BlogIndexPage, BlogPageGalleryImage

class BlogPageSerializer(serializers.ModelSerializer):
    main_image_url = serializers.SerializerMethodField()

    class Meta:
        model = BlogPage
        fields = ["id", "title", "date", "intro", "body", "main_image_url"]

    def get_main_image_url(self, obj):
        """Returns the first image URL from the gallery if available"""
        main_image = obj.main_image()
        if main_image:
            return main_image.get_rendition("fill-800x450").url
        return None

class BlogPageViewSet(viewsets.ModelViewSet):
    serializer_class = BlogPageSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return BlogPage.objects.live().public().order_by("-first_published_at")

    def perform_create(self, serializer):
        """Creates a new BlogPage, attaches an image if provided, and publishes it"""
        try:
            # ✅ Get the first BlogIndexPage
            blog_index = BlogIndexPage.objects.first()
            if not blog_index:
                raise serializers.ValidationError({"error": "No BlogIndexPage found! Create one in Wagtail Admin."})

            validated_data = serializer.validated_data
            image_url = self.request.data.get("main_image_url")  # ✅ Get image URL from request

            # ✅ Create BlogPage instance
            new_blog_page = BlogPage(
                title=validated_data["title"],
                intro=validated_data["intro"],
                body=validated_data["body"],
                date=validated_data["date"],
            )

            # ✅ Add to BlogIndexPage
            blog_index.add_child(instance=new_blog_page)
            new_blog_page.save()  # Save the blog page first

            # ✅ If an external image URL is provided, download and attach it to the gallery
            if image_url:
                response = requests.get(image_url)
                if response.status_code == 200:
                    filename = image_url.split("/")[-1]
                    image_content = ContentFile(response.content, name=filename)

                    # ✅ Create & Save the Image in Wagtail
                    wagtail_image = Image(title=new_blog_page.title)
                    wagtail_image.file.save(filename, image_content, save=True)

                    # ✅ Attach image to the gallery
                    BlogPageGalleryImage.objects.create(page=new_blog_page, image=wagtail_image)

            # ✅ Publish the blog post
            new_blog_page.save_revision().publish()

            # ✅ Assign instance to serializer
            serializer.instance = new_blog_page

        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})