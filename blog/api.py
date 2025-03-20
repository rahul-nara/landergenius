from rest_framework import serializers, viewsets, status
from rest_framework.response import Response
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
            blog_index = BlogIndexPage.objects.first()
            if not blog_index:
                raise serializers.ValidationError({"error": "No BlogIndexPage found! Create one in Wagtail Admin."})

            validated_data = serializer.validated_data
            image_url = self.request.data.get("main_image_url")

            new_blog_page = BlogPage(
                title=validated_data["title"],
                intro=validated_data["intro"],
                body=validated_data["body"],
                date=validated_data["date"],
            )

            blog_index.add_child(instance=new_blog_page)
            new_blog_page.save()

            if image_url:
                response = requests.get(image_url)
                if response.status_code == 200:
                    filename = image_url.split("/")[-1]
                    image_content = ContentFile(response.content, name=filename)
                    wagtail_image = Image(title=new_blog_page.title)
                    wagtail_image.file.save(filename, image_content, save=True)
                    BlogPageGalleryImage.objects.create(page=new_blog_page, image=wagtail_image)

            new_blog_page.save_revision().publish()
            serializer.instance = new_blog_page
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})

    def update(self, request, pk=None):
        """Handles PUT requests for updating a BlogPage"""
        try:
            blog_page = BlogPage.objects.get(pk=pk)
            serializer = self.get_serializer(blog_page, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                blog_page.save_revision().publish()  # Save and publish the update
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except BlogPage.DoesNotExist:
            return Response({"error": "BlogPage not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """Handles DELETE requests for deleting a BlogPage"""
        try:
            blog_page = BlogPage.objects.get(pk=pk)
            blog_page.delete()  # Soft delete in Wagtail
            return Response({"message": "BlogPage deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

        except BlogPage.DoesNotExist:
            return Response({"error": "BlogPage not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
