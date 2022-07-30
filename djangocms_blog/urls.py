from django.conf.urls import url

from .feeds import FBInstantArticles, LatestEntriesFeed, TagFeed
from .settings import get_setting
from .views import (
    AuthorEntriesView,
    CategoryEntriesView,
    PostArchiveView,
    PostDetailView,
    PostListView,
    TaggedListView,
)


def get_urls():
    urls = get_setting("PERMALINK_URLS")
    return [
        url(urlconf, PostDetailView.as_view(), name="post-detail")
        for urlconf in urls.values()
    ]


detail_urls = get_urls()

# module-level app_name attribute as per django 1.9+
app_name = "djangocms_blog"
urlpatterns = [
    url(r"^$", PostListView.as_view(), name="posts-latest"),
    url(r"^feed/$", LatestEntriesFeed(), name="posts-latest-feed"),
    url(r"^feed/fb/$", FBInstantArticles(), name="posts-latest-feed-fb"),
    url(r"^(?P<year>\d{4})/$", PostArchiveView.as_view(), name="posts-archive"),
    url(r"^(?P<year>\d{4})/(?P<month>\d{1,2})/$", PostArchiveView.as_view(), name="posts-archive"),
    url(r"^author/(?P<username>[\w\.@+-]+)/$", AuthorEntriesView.as_view(), name="posts-author"),
    url(r"^category/(?P<category>[\w\.@+-]+)/$", CategoryEntriesView.as_view(), name="posts-category"),
    url(r"^tag/(?P<tag>[-\w]+)/$", TaggedListView.as_view(), name="posts-tagged"),
    url(r"^tag/(?P<tag>[-\w]+)/feed/$", TagFeed(), name="posts-tagged-feed"),
] + detail_urls
