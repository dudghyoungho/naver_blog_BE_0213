"""
URL configuration for naver_blog project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, re_path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from main.views.signup import SignupView
from main.views.login import LoginView
from main.views.logout import LogoutView
from main.views.account import PasswordUpdateView
from main.views.profile import ProfileDetailView, ProfilePublicView, ProfileUrlnameUpdateView
from main.views.post import PostDetailView,PostMyView,PostMyDetailView,PostMutualView,PostManageView,PostListView,PostCreateView,DraftPostListView,DraftPostDetailView, PostMyCurrentView, PostPublicCurrentView, PostCountView
from main.views.comment import CommentListView, CommentDetailView
from main.views.heart import ToggleHeartView, PostHeartUsersView, PostHeartCountView
from main.views.commentHeart import ToggleCommentHeartView, CommentHeartCountView
from main.views.neighbor import NeighborView,NeighborAcceptView,NeighborRejectView,NeighborRequestListView,PublicNeighborListView, MyNeighborListView, MyNeighborDeleteView, NeighborNumberView
from main.views.news import MyNewsListView
from main.views.activity import MyActivityListView
from main.views.search import BlogPostSearchView, GlobalBlogSearchView, GlobalNickAndIdSearchView, GlobalPostSearchView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny

# 간소화된 Swagger 설정
schema_view = get_schema_view(
    openapi.Info(
        title="Naver Blog API",
        default_version='v1',
        description="Naver Blog API Documentation",
    ),
    public=True,
    permission_classes=(AllowAny,),
)
urlpatterns = [
    path('admin/', admin.site.urls),

    # ✅ 회원가입 API
    path('signup/', SignupView.as_view(), name='signup'),
    # ✅ 로그인 및 로그아웃 API
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password/update/', PasswordUpdateView.as_view(), name='password-update'),


    # ✅ 내 프로필 관련 API
    path('profile/me/', ProfileDetailView.as_view(), name='profile-me'),  # 내 프로필 조회, 수정, 삭제
    path("profile/me/neighbors/<str:neighbor_urlname>/", MyNeighborDeleteView.as_view(), name="my-neighbor-delete"),# 내 서로이웃 삭제
    path("profile/me/neighbors/", MyNeighborListView.as_view(), name="my-neighbor-list"), # 내 서로이웃 목록 확인 (로그인한 사용자)
    path('profile/urlname/', ProfileUrlnameUpdateView.as_view(), name='profile-urlname-update'),  # urlname 변경 (한 번만 가능)

    # 내 소식 및 내 활동 관련 API
    path('news/list/', MyNewsListView.as_view(), name='my-news-list'), # 내 소식
    path('activity/list/', MyActivityListView.as_view(), name='my-activity-list'), # 내 활동

    # ✅ 타인 프로필 관련 API
    path('profile/<str:urlname>/', ProfilePublicView.as_view(), name='profile-public'),
    path('profile/<str:urlname>/neighbors/', PublicNeighborListView.as_view(), name='neighbor-list'),


    # ✅ 서로이웃 관련 API
    path("neighbors/<str:to_urlname>/", NeighborView.as_view(), name="neighbor-request"),
    path('neighbors/requests/me', NeighborRequestListView.as_view(), name='neighbor-request-list'),
    path('neighbors/accept/<str:from_urlname>/', NeighborAcceptView.as_view(), name='neighbor-accept'),
    path('neighbors/reject/<str:from_urlname>/', NeighborRejectView.as_view(), name='neighbor-reject'),
    path('neighbors/count/<str:urlname>/', NeighborNumberView.as_view(), name='neighbor-count'),

    # 게시물 검색 관련 API (블로그 내 검색)
    path('search/blog/', BlogPostSearchView.as_view(), name='blog-post-search'),
    path('search/global-blog/', GlobalBlogSearchView.as_view(), name='global-blog-search'),
    path('search/global-nickandid/', GlobalNickAndIdSearchView.as_view(), name='global-nickandid-search'),
    path('search/global-post/', GlobalPostSearchView.as_view(), name='global-post-search'),

    # ✅ 게시물 관련 API

    # 내 게시물 관련 API
    path('posts/me/', PostMyView.as_view(), name='post-my-list'),  # 내가 작성한 게시물 목록 조회, 쿼리 파라미터 활용!
    path('posts/me/<int:pk>/', PostMyDetailView.as_view(), name='post-my-detail'),  # 내가 작성한 게시물 상세 조회
    path('posts/me/create/', PostCreateView.as_view(), name='post-create'),  # 게시물 생성 (POST)
    path('posts/me/<int:pk>/manage/', PostManageView.as_view(), name='post-manage'),  # 게시물 수정/삭제 (PUT, PATCH, DELETE)
    path('posts/me/current/', PostMyCurrentView.as_view(), name='post-my-current'), # 내가 작성한 게시물 목록 최신 5개 조회

    # 게시물 개수 세기
    path('posts/count/<str:urlname>/', PostCountView.as_view(), name='post-count'),

    #타인 게시물 관련 API

    path('posts/', PostListView.as_view(), name='post-list'),  # 타인 게시물 목록 조회 (GET, 쿼리 파라미터 활용)
    path('posts/<int:pk>/', PostDetailView.as_view(), name='post-detail'),  # 타인 게시물 상세 조회 (GET)
    path('posts/<str:urlname>/current/', PostPublicCurrentView.as_view(), name='post-public-recent'),

    #서로 이웃 새글 API
    path('posts/mutual/recentweekly', PostMutualView.as_view(), name='post-mutual'),

    #임시 저장된 게시물 관련 API
    path('posts/drafts/', DraftPostListView.as_view(), name='draft_post_list'),  # 임시 저장된 게시물 목록 조회
    path('posts/drafts/<int:pk>/', DraftPostDetailView.as_view(), name='draft_post_detail'),  # 임시 저장된 게시물 상세 조회

    # ✅ 특정 게시글의 댓글 목록 조회 & 댓글 작성
    path('posts/<int:post_id>/comments/', CommentListView.as_view(), name='comment-list'),
    path('posts/<int:post_id>/comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),

    # ✅ 공감(좋아요) 관련 API

    # 게시글 좋아요 추가/삭제
    path('posts/<int:post_id>/heart/', ToggleHeartView.as_view(), name='toggle-heart'),
    # 게시글 좋아요 누른 유저 목록 조회
    path('posts/<int:post_id>/heart/users/', PostHeartUsersView.as_view(), name='post-heart-users'),
    # 게시글 좋아요 개수 조회
    path('posts/<int:post_id>/heart/count/', PostHeartCountView.as_view(), name='post-heart-count'),

    # 댓글/대댓글 좋아요 추가/삭제
    path('posts/<int:post_id>/comments/<int:comment_id>/heart/', ToggleCommentHeartView.as_view(),
         name='toggle-comment-heart'),
    # 댓글/대댓글 좋아요 개수 조회
    path('posts/<int:post_id>/comments/<int:comment_id>/heart/count/', CommentHeartCountView.as_view(),
         name='comment-heart-count'),
    # Swagger 관련 경로 (drf-yasg 사용)
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),  # ReDoc UI 추가
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

]

# 미디어 파일 처리 (개발 환경에서만)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
