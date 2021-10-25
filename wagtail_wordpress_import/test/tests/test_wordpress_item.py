import os
import json
from django.test import TestCase, override_settings
from datetime import datetime
from example.models import Category
from wagtail.core.models import Page
from wagtail_wordpress_import.importers.wordpress import (
    WordpressImporter,
    WordpressItem,
)
from wagtail_wordpress_import.logger import Logger


BASE_PATH = os.path.dirname(os.path.dirname(__file__))
FIXTURES_PATH = BASE_PATH + "/fixtures"
LOG_DIR = "fakedir"
IMPORTER_RUN_PARAMS_TEST = {
    "app_for_pages": "example",
    "model_for_pages": "TestPage",
    "parent_id": "2",
    "page_types": ["post", "page"],
    "page_statuses": ["publish", "draft"],
}

class WordpressItemTests(TestCase):
    def setUp(self):
        self.logger = Logger("fakedir")
        raw_html_file = open(f"{FIXTURES_PATH}/raw_html.txt", "r").read()
        self.good_node = {
            "title": "Page Title",
            "wp:post_name": "page-title",
            "wp:post_date_gmt": "2017-03-12 17:53:57",
            "wp:post_modified_gmt": "2018-12-04 11:49:24",
            "content:encoded": raw_html_file,
            "wp:post_id": "1000",
            "wp:post_type": "post",
            "link": "http://www.example.com",
        }
        self.bad_node = {
            "title": "Page Title",
            "wp:post_name": "",
            "wp:post_date_gmt": "0000-00-00 00:00:00",
            "wp:post_modified_gmt": "0000-00-00 00:00:00",
            "content:encoded": raw_html_file,
            "wp:post_id": "1000",
            "wp:post_type": "post",
            "link": "",
        }

    def test_all_fields_with_good_data(self):
        wordpress_item = WordpressItem(self.good_node, self.logger)
        title = wordpress_item.cleaned_data["title"]
        slug = wordpress_item.cleaned_data["slug"]
        first_published_at = wordpress_item.cleaned_data["first_published_at"]
        last_published_at = wordpress_item.cleaned_data["last_published_at"]
        latest_revision_created_at = wordpress_item.cleaned_data[
            "latest_revision_created_at"
        ]
        # the body content here will have all attrs, classes etc stripped
        # by the bleach filter
        body = wordpress_item.cleaned_data["body"]
        wp_post_id = wordpress_item.cleaned_data["wp_post_id"]
        wp_post_type = wordpress_item.cleaned_data["wp_post_type"]
        wp_link = wordpress_item.cleaned_data["wp_link"]
        wp_raw_content = wordpress_item.debug_content["filter_linebreaks_wp"]
        wp_processed_content = wordpress_item.debug_content[
            "filter_transform_inline_styles"
        ]
        wp_block_json = wordpress_item.debug_content["block_json"]

        self.assertEqual(title, "Page Title")
        self.assertEqual(slug, "page-title")
        self.assertIsInstance(first_published_at, datetime)
        self.assertIsInstance(last_published_at, datetime)
        self.assertIsInstance(latest_revision_created_at, datetime)
        self.assertIsInstance(json.dumps(body), str)
        self.assertEqual(wp_post_id, 1000)
        self.assertEqual(wp_post_type, "post")
        self.assertEqual(wp_link, "http://www.example.com")
        self.assertIsInstance(wp_raw_content, str)
        self.assertIsInstance(wp_processed_content, str)
        self.assertIsInstance(wp_block_json, list)

    def test_cleaned_fields(self):
        wordpress_item = WordpressItem(self.bad_node, self.logger)
        slug = wordpress_item.cleaned_data["slug"]
        first_published_at = wordpress_item.cleaned_data["first_published_at"]
        last_published_at = wordpress_item.cleaned_data["last_published_at"]
        latest_revision_created_at = wordpress_item.cleaned_data[
            "latest_revision_created_at"
        ]
        wp_link = wordpress_item.cleaned_data["wp_link"]
        self.assertEqual(slug, "page-title")
        self.assertIsInstance(first_published_at, datetime)
        self.assertIsInstance(last_published_at, datetime)
        self.assertIsInstance(latest_revision_created_at, datetime)
        self.assertEqual(wp_link, "")


@override_settings(
    BASE_URL="http://localhost:8000",
    WAGTAIL_WORDPRESS_IMPORT_CATEGORY_PLUGIN_ENABLED=True,
    WAGTAIL_WORDPRESS_IMPORT_CATEGORY_PLUGIN_MODEL="example.models.Category",
)  # testing requires a live domain for requests to use, this is something I need to change before package release
# mocking of somesort, using localhost:8000 for now
class WordpressItemImportTests(TestCase):
    from example.models import Category

    fixtures = [
        f"{FIXTURES_PATH}/dump.json",
    ]

    def setUp(self):
        self.importer = WordpressImporter(f"{FIXTURES_PATH}/raw_xml.xml")
        self.logger = Logger(LOG_DIR)
        self.importer.run(
            logger=self.logger,
            app_for_pages=IMPORTER_RUN_PARAMS_TEST["app_for_pages"],
            model_for_pages=IMPORTER_RUN_PARAMS_TEST["model_for_pages"],
            parent_id=IMPORTER_RUN_PARAMS_TEST["parent_id"],
            page_types=IMPORTER_RUN_PARAMS_TEST["page_types"],
            page_statuses=IMPORTER_RUN_PARAMS_TEST["page_statuses"],
        )

        self.parent_page = Page.objects.get(id=IMPORTER_RUN_PARAMS_TEST["parent_id"])
        self.imported_pages = self.parent_page.get_children().all()

    def test_category_snippets_are_saved(self):
        snippets = Category.objects.all()
        self.assertEqual(len(snippets), 4)

    def test_page_has_categories(self):
        page_one = self.imported_pages.get(title="Item one title")
        page_one_categories = page_one.specific.categories.all()
        self.assertEqual(2, page_one_categories.count())

        page_two = self.imported_pages.get(title="Item two title")
        page_two_categories = page_two.specific.categories.all()
        self.assertEqual(2, page_two_categories.count())
