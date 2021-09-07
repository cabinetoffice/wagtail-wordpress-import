import json
# import os
import xml.etree.ElementTree as ET

from django.core.management.base import BaseCommand

from wagtail_xmlimport.cls.cls import PathsToDict

# register all namespaces to keep them when the modified xml is saved
def register_all_namespaces(filename):
    namespaces = dict([node for _, node in ET.iterparse(filename, events=["start-ns"])])
    for ns in namespaces:
        ET.register_namespace(ns, namespaces[ns])


class Command(BaseCommand):

    help = """Utils to reduce xml file size by removing unwanted tags."""

    def __init__(self, *args, **kwargs):
        self.xml_folder_path = "xml"
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument("xmlfile", type=str)

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Reducing ..."))
        self.stdout.write(
            self.style.NOTICE(
                "If this is a large file and has many depths it will take some time to complete"
            )
        )
        file_name = options["xmlfile"]
        file_path = f"{self.xml_folder_path}/{file_name}"
        # xml = open(f"{self.xml_folder_path}/{file_name}", "rb").read()
        register_all_namespaces(file_path)

        num_lines_original = sum(1 for line in open(file_path))
        num_lines_original_formatted = "{:,}".format(num_lines_original)

        self.stdout.write(f"Original #lines {num_lines_original_formatted}")

        ofile = file_name.split(".")[0]
        output_file_name = f"{ofile}-reduced.xml"
        output_file_path = f"{self.xml_folder_path}/{output_file_name}"

        tree = ET.parse(file_path)
        wp = "{http://wordpress.org/export/1.2/}"
        items = tree.getroot()[0].findall("item")
        for item in items:
            comments = item.findall(f"{wp}comment")
            for comment in comments:
                item.remove(comment)

        tree.write(output_file_path)

        num_lines_out = sum(1 for line in open(output_file_name))
        num_lines_out_formatted = "{:,}".format(num_lines_out)

        num_lines_diff = num_lines_original - num_lines_out
        num_lines_diff_formatted = "{:,}".format(num_lines_diff)

        self.stdout.write(f"Output #lines {num_lines_out_formatted}")
        
        self.stdout.write(f"Saved #{num_lines_diff_formatted} lines")

        self.stdout.write(
            self.style.SUCCESS(f"Finished Your file is here: {output_file_name}")
        )
