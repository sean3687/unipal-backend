from pymongo import MongoClient
from dotenv import load_dotenv
import os
import requests
import json


class preRequisiteTree:
    def __init__(self):
        load_dotenv()
        self.mongo_uri = os.getenv("MONGO_URI")
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client["Course-Database"]
        self.courseSource = os.getenv("course_source")
        self.response = requests.get(self.courseSource)
        self.courseData = self.response.json()
        self.preRequisiteCourseData = {}
        self.finalList = []
        self.course_tree_collection = self.db["CoursePrerequisiteTree"]

    def convertString_to_dict(self):
        """Process each course's prerequisite information."""
        for course in self.courseData:
            # print(course['prerequisite_tree'])  # Check what the content looks like
            if course["prerequisite_tree"]:  # Ensure it's not empty
                    data = json.loads(course["prerequisite_tree"])
                    prerequisites = self.expand_conditions(data)
                    self.finalList.append(
                        {
                            "id": course["id"],
                            "title": course["title"],
                            "prerequisiteTree": course.get("prerequisite_tree", ""),
                            "prerequisites": prerequisites,
                            "preRequisiteDetails" : course["prerequisite_text"],
                            "department_name": course['department_name'],
                            "course_level":course['course_level'],
                            
                        }
                    )
            else:
                    self.finalList.append(
                        {
                            "id": course["id"],
                            "title":course["title"],
                            "prerequisiteTree": [],
                            "prerequisites": [],
                            "preRequisiteDetails" : course["prerequisite_text"],
                            "department_name": course['department_name'],
                            "course_level":course['course_level']
                        }
                    )


    def combine_and(self, lists):
        """Combine prerequisites using cartesian product for 'AND' conditions."""
        if not lists:
            return [[]]
        first, *rest = lists
        result = []
        for item in first:
            for suffix in self.combine_and(rest):
                result.append(
                    item + suffix if isinstance(suffix, list) else [item] + suffix
                )
        return result

    def expand_conditions(self, data):
        """Recursively expand the conditions based on 'AND' and 'OR' operators."""
        if isinstance(data, str):
            return [[data]]  # Encapsulate strings in lists to handle uniformly
        if "OR" in data:
            return sum((self.expand_conditions(option) for option in data["OR"]), [])
        if "AND" in data:
            expanded_lists = [self.expand_conditions(sub) for sub in data["AND"]]
            return self.combine_and(expanded_lists)

    def addIntoDatabase(self):
        """The function adds prerequisite course data into a database collection."""
        result = self.course_tree_collection.insert_many(self.finalList)
        return len(result.inserted_ids) == len(self.finalList)

    def print_preRequisiteCourseData(self):
        print(len(self.finalList))


tree_instance = preRequisiteTree()
tree_instance.convertString_to_dict()
tree_instance.print_preRequisiteCourseData()
print(tree_instance.addIntoDatabase())
