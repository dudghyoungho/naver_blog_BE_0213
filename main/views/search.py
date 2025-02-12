from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models.post import Post, PostText, PostImage  # 🔹 PostImage 추가
from ..models.profile import Profile
from ..serializers.search import PostSearchSerializer


def is_mutual_friend(user, author):
    """
    사용자가 게시글 작성자와 서로 이웃인지 확인하는 함수.
    소셜 관계 구현 방식에 따라 이 부분을 수정해야 할 수도 있음.
    """
    if not user.is_authenticated:
        return False  # 로그인하지 않은 사용자는 서로 이웃이 아님

    return user.following.filter(id=author.id).exists()  # 'following' 필드는 예시


def get_excerpt(text, keyword, context_length=30):
    """
    본문에서 키워드 앞뒤 지정된 길이(context_length)만큼을 포함한 발췌(excerpt) 반환
    """
    keyword_index = text.lower().find(keyword.lower())
    if keyword_index == -1:
        return text[:context_length * 2]  # 키워드가 없으면 앞부분 일부 반환

    start = max(0, keyword_index - context_length)
    end = min(len(text), keyword_index + len(keyword) + context_length)

    return text[start:end] + ("..." if end < len(text) else "")


class BlogPostSearchView(APIView):
    """
    특정 블로그 내에서 게시글을 검색하는 API
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_summary = "특정 블로그 게시물 검색",
        operation_description="특정 블로그 내에서 게시물을 검색합니다.",
        manual_parameters=[
            openapi.Parameter('urlname', openapi.IN_QUERY, description="블로그 식별자 (사용자 프로필 URL 식별자)",
                              type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('q', openapi.IN_QUERY, description="검색어", type=openapi.TYPE_STRING, required=True),
        ],
        responses={200: PostSearchSerializer(many=True)}
    )
    def get(self, request):
        search_keyword = request.GET.get('q', '').strip()
        urlname = request.GET.get('urlname', '').strip()  # 블로그 식별자 (필수 입력)

        if not urlname:
            return Response({"error": "urlname(블로그 식별자)을 입력해주세요."}, status=400)

        if not search_keyword or len(search_keyword) < 2:
            return Response({"error": "검색어는 2글자 이상 입력해주세요."}, status=400)

        # 🔹 urlname을 통해 해당 블로그(사용자) 찾기
        try:
            blog_owner = Profile.objects.get(urlname=urlname).user  # Profile 모델에서 사용자 찾기
        except Profile.DoesNotExist:
            return Response({"error": "해당 urlname에 해당하는 블로그가 없습니다."}, status=404)

        user = request.user  # 현재 검색을 요청한 사용자

        # 🔹 제목 검색 (나만 보기, 서로 이웃 필터링)
        title_matches = Post.objects.filter(
            Q(title__icontains=search_keyword) & Q(author=blog_owner) & ~Q(visibility='me')
        )

        # 🔹 본문 검색 (나만 보기, 서로 이웃 필터링)
        content_matches = PostText.objects.filter(
            Q(content__icontains=search_keyword) & Q(post__author=blog_owner) & ~Q(post__visibility='me')
        ).select_related('post')

        # 🔹 이미지 캡션 검색 (나만 보기, 서로 이웃 필터링)
        caption_matches = PostImage.objects.filter(
            Q(caption__icontains=search_keyword) & Q(post__author=blog_owner) & ~Q(post__visibility='me')
        ).select_related('post')

        # 🔹 검색된 게시물 ID 저장 (중복 제거)
        matched_post_ids = (
            set(title_matches.values_list('id', flat=True))
            | set(content_matches.values_list('post_id', flat=True))
            | set(caption_matches.values_list('post_id', flat=True))  # 🔹 이미지 설명 포함
        )

        # 🔹 검색된 게시물 조회 (서로 이웃 필터링 적용)
        posts = Post.objects.filter(id__in=matched_post_ids).prefetch_related('texts', 'images', 'author')

        results = []
        for post in posts:
            if post.visibility == 'mutual' and not is_mutual_friend(user, post.author):
                continue  # 서로 이웃이 아닐 경우 검색 결과에서 제외

            thumbnail = post.images.filter(is_representative=True).first()
            thumbnail_url = thumbnail.image.url if thumbnail else None

            excerpt = ""
            for text in post.texts.all():
                if search_keyword.lower() in text.content.lower():
                    excerpt = get_excerpt(text.content, search_keyword)
                    break

            results.append({
                "title": post.title,
                "created_at": post.created_at.strftime("%Y-%m-%d %H:%M"),
                "thumbnail": thumbnail_url,
                "excerpt": excerpt,
            })

        return Response({"results": results})

class GlobalBlogSearchView(APIView):
    """
    전체 블로그에서 블로그명을 검색하는 API
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_summary="블로그명 검색 (전체)",
        operation_description="블로그명을 검색하여 관련 블로그 정보를 반환합니다.",
        manual_parameters=[
            openapi.Parameter('q', openapi.IN_QUERY, description="검색할 블로그명", type=openapi.TYPE_STRING, required=True),
        ],
        responses={200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "blogs": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_OBJECT)
                )
            }
        )}
    )
    def get(self, request):
        search_keyword = request.GET.get('q', '').strip()

        if not search_keyword or len(search_keyword) < 2:
            return Response({"error": "검색어는 2글자 이상 입력해주세요."}, status=400)

        # 🔹 `blog_name`을 기준으로 검색
        blog_matches = Profile.objects.filter(Q(blog_name__icontains=search_keyword))

        results = [
            {
                "username": profile.user.username,
                "urlname": profile.urlname,
                "blog_name": profile.blog_name,
                "intro": profile.intro,  # 🔹 블로그 한 줄 소개 추가
                "user_pic": profile.user_pic.url if profile.user_pic else None  # 🔹 사용자 프로필 사진 추가
            }
            for profile in blog_matches
        ]

        return Response({"blogs": results})

class GlobalNickAndIdSearchView(APIView):
    """
    전체 블로그에서 사용자명(username) 및 블로그 ID(urlname)를 검색하는 API
    - urlname이 정확히 일치하는 사용자가 있다면 최상단에 위치
    - username이 검색어를 포함하는 사용자는 그 아래에 리스트 형태로 제공
    - urlname과 username이 같은 경우 중복 방지
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_summary="사용자명, 블로그 url 검색(전체)",
        operation_description="사용자명(username) 또는 블로그 ID(urlname)을 검색합니다.",
        manual_parameters=[
            openapi.Parameter('q', openapi.IN_QUERY, description="검색할 사용자명 또는 블로그 ID", type=openapi.TYPE_STRING, required=True),
        ],
        responses={200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "users": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_OBJECT)
                )
            }
        )}
    )
    def get(self, request):
        search_keyword = request.GET.get('q', '').strip()

        if not search_keyword or len(search_keyword) < 2:
            return Response({"error": "검색어는 2글자 이상 입력해주세요."}, status=400)

        results = []
        urlname_matched_user_id = None  # 중복 방지용 변수

        # 🔹 1. `urlname`이 정확히 일치하는 사용자 찾기 (중복 불가)
        try:
            exact_match = Profile.objects.get(urlname=search_keyword)
            results.append({
                "username": exact_match.username,  # ✅ Profile.username 사용
                "urlname": exact_match.urlname,
                "blog_name": exact_match.blog_name,
                "intro": exact_match.intro,
                "user_pic": exact_match.user_pic.url if exact_match.user_pic else None
            })
            urlname_matched_user_id = exact_match.id  # 🔹 해당 사용자의 ID 저장 (중복 방지)
        except Profile.DoesNotExist:
            pass  # 정확히 일치하는 `urlname`이 없을 경우 아무것도 하지 않음

        # 🔹 2. `username`이 포함된 사용자 검색 (중복 가능) → `urlname`과 중복되는 사용자는 제외
        username_matches = Profile.objects.filter(
            Q(username__icontains=search_keyword)
        ).exclude(id=urlname_matched_user_id)

        results += [
            {
                "username": profile.username,  # ✅ Profile.username 사용
                "urlname": profile.urlname,
                "blog_name": profile.blog_name,
                "intro": profile.intro,
                "user_pic": profile.user_pic.url if profile.user_pic else None
            }
            for profile in username_matches
        ]

        return Response({"users": results})



class GlobalPostSearchView(APIView):
    """
    전체 블로그에서 게시글을 검색하는 API
    - 게시글 제목, 본문, 이미지 캡션에서 검색
    - 같은 게시물이 중복으로 반환되지 않도록 처리
    - 전체 공개(visibility='everyone') 게시글만 포함
    - 검색된 키워드 주변 텍스트를 포함한 미리보기(excerpt) 제공
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_summary="블로그 글 검색 (전체)",
        operation_description="전체 블로그에서 게시글을 검색합니다.",
        manual_parameters=[
            openapi.Parameter('q', openapi.IN_QUERY, description="검색할 키워드", type=openapi.TYPE_STRING,
                              required=True),
        ],
        responses={200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "posts": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_OBJECT)
                )
            }
        )}
    )
    def get(self, request):
        search_keyword = request.GET.get('q', '').strip()

        if not search_keyword or len(search_keyword) < 2:
            return Response({"error": "검색어는 2글자 이상 입력해주세요."}, status=400)

        matched_post_ids = set()
        excerpts = {}  # 🔹 post_id 별 excerpt 저장

        # 🔹 1. 제목에서 검색 (중복 방지 & 전체 공개 필터링)
        title_matches = Post.objects.filter(
            Q(title__icontains=search_keyword) & Q(visibility='everyone')
        )
        matched_post_ids.update(title_matches.values_list('id', flat=True))

        # 🔹 2. 본문에서 검색 (중복 방지 & 전체 공개 필터링)
        content_matches = PostText.objects.filter(
            Q(content__icontains=search_keyword) & Q(post__visibility='everyone')
        ).select_related('post')

        for text in content_matches:
            post_id = text.post.id
            matched_post_ids.add(post_id)
            if post_id not in excerpts:
                excerpts[post_id] = get_excerpt(text.content, search_keyword)  # ✅ 기존 함수 사용

        # 🔹 3. 이미지 캡션에서 검색 (중복 방지 & 전체 공개 필터링)
        caption_matches = PostImage.objects.filter(
            Q(caption__icontains=search_keyword) & Q(post__visibility='everyone')
        ).select_related('post')

        for image in caption_matches:
            post_id = image.post.id
            matched_post_ids.add(post_id)
            if post_id not in excerpts:
                excerpts[post_id] = get_excerpt(image.caption, search_keyword)  # ✅ 기존 함수 사용

        # 🔹 4. 검색된 게시물 조회 (중복 제거됨)
        posts = Post.objects.filter(id__in=matched_post_ids).select_related('author__profile')

        results = []
        for post in posts:
            profile = post.author.profile
            results.append({
                "title": post.title,
                "username": post.author.username,
                "blog_name": profile.blog_name,
                "created_at": post.created_at.strftime("%Y-%m-%d %H:%M"),
                "excerpt": excerpts.get(post.id, post.title)  # 🔹 기본값: 제목
            })

        return Response({"posts": results})
