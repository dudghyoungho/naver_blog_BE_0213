from rest_framework import serializers
from ..models import Post, PostText, PostImage  # 🔹 PostImage 추가


class PostSearchSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()
    excerpt = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['title', 'created_at', 'thumbnail', 'excerpt']

    def get_thumbnail(self, obj):
        """
        대표 이미지를 반환. 없으면 None 반환
        """
        thumbnail = obj.images.filter(is_representative=True).first()
        return thumbnail.image.url if thumbnail else None

    def get_excerpt(self, obj):
        """
        본문 및 사진 설명에서 검색어 앞뒤 일부를 포함한 내용 반환
        """
        request = self.context.get('request')
        search_keyword = request.GET.get('q', '') if request else ''

        if not search_keyword:
            return ""

        # 본문 검색
        for text in obj.texts.all():
            if search_keyword.lower() in text.content.lower():
                return self.extract_excerpt(text.content, search_keyword)

        # 이미지 설명 검색 (본문에서 검색어를 찾지 못한 경우)
        for image in obj.images.all():
            if image.caption and search_keyword.lower() in image.caption.lower():
                return self.extract_excerpt(image.caption, search_keyword)

        return ""

    def extract_excerpt(self, text, keyword, context_length=30):
        """
        텍스트에서 키워드 앞뒤 30자 포함한 일부 텍스트 반환
        """
        keyword_index = text.lower().find(keyword.lower())
        if keyword_index == -1:
            return text[:context_length * 2]  # 키워드가 없으면 앞부분 일부 반환

        start = max(0, keyword_index - context_length)
        end = min(len(text), keyword_index + len(keyword) + context_length)

        return text[start:end] + ("..." if end < len(text) else "")
