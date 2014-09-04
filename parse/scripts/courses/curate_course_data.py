import httplib
import urllib
import xml.etree.ElementTree as ET
import json
import sys

term = ''
pp_id = ""
rest_api_key = ""

PARSE_API_URL = 'api.parse.com'
PARSE_API_PORT = 443
COURSES_ENDPOINT = '/1/classes/Course'

def read_data(term):
  """
  Given the specific term, retreives the XML describing all of the courses for a given semester.

  Example input:
  term = '201420'
  """
  course_url = '/admweb/!SWKSECX.main?term='+ term + '&title=&course=&crn=&coll=&dept=&subj='
  connection = httplib.HTTPSConnection('courses.rice.edu', 443)
  connection.connect()
  connection.request(
    'GET',
    course_url
  )
  courses_xml = connection.getresponse()
  return courses_xml

def read_courses_tree(filename):
  f_in = open(filename, 'r')
  courses_tree = ET.fromstring(f_in.read())
  return courses_tree

def to_camel_case(string):
  out_str = ""
  capitalize = False
  for c in string:
    if c == '-':
      capitalize = True
      continue
    if capitalize:
      out_str += c.upper()
      capitalize = False
    else:
      out_str += c
  return out_str

def pull_attributes_from_xml(xml_element, attributes):
  obj = {}
  for attr in attributes:
    attr_elem = xml_element.find(attr)
    if attr_elem is not None:
      obj[to_camel_case(attr)] = attr_elem.text
    else:
      obj[to_camel_case(attr)] = None
  return obj

def parse_create_course(xml_course):
  """
  Uses the information in the XML to create a Course object to send to Parse
  """
  attrs = [
    "term-code",
    "term-description",
    'subject',
    "course-number",
    "school",
    "department",
    "title",
    "description",
    "credit-hours",
    "distribution-group"
  ]
  return pull_attributes_from_xml(xml_course, attrs)

def parse_get_course(xml_course):
  """
  Uses the information in the XML to find an existing course in the parse database by doing a look up using subject and course-number
  """
  parse_course = parse_create_course(xml_course)
  query_constraints = {
    "termCode": parse_course["termCode"],
    "subject": parse_course["subject"],
    "courseNumber": parse_course["courseNumber"]
  }
  params = urllib.urlencode({"where": json.dumps(query_constraints)})
  connection = httplib.HTTPSConnection(PARSE_API_URL, PARSE_API_PORT)
  connection.connect()
  connection.request(
    "GET",
    "%s?%s" % (COURSES_ENDPOINT, params),
    '',
    {"X-Parse-Application-Id": pp_id, "X-Parse-REST-API-Key": rest_api_key}
  )
  response = json.loads(connection.getresponse().read())
  if response.get("results"):
    return response["results"][0]
  else:
    return None


def upload_course(parse_course):
  """
  Given Course data, creates or updates the Parse Course for it. Returns the id of the object uploaded.
  """
  # If parse_course["id"] is not specified, use POST method otherwise use PUT and return the upload results
  # If upload fails, throw an exception because the user of this function relies on this function succeeding
  url = COURSES_ENDPOINT
  if not parse_course.get("objectId"):
    method = "POST"
  else:
    method = "PUT"
    url += '/' + parse_course["objectId"]

  connection = httplib.HTTPSConnection(PARSE_API_URL, PARSE_API_PORT)
  connection.connect()
  connection.request(
    method,
    url,
    json.dumps(parse_course),
    {"X-Parse-Application-Id": pp_id, "X-Parse-REST-API-Key": rest_api_key}
  )
  result = json.loads(connection.getresponse().read())
  if method == "POST":
    return result["objectId"]
  else:
    return parse_course["objectId"]



def parse_create_section(xml_course):
  """
  Uses the information in the XML to create a Section object to send to Parse
  """

  section = {}
  section["courseNumber"] = course.get("course-number")
  section["sectionNumber"] = course.get("section")
  section["crn"] = course.get("crn")
  section["startTime"] = course.get("start-time")
  section["endTime"] = course.get("end-time")
  section["meetingDays"] = course.get("meeting-days")
  section["locations"] = course.get("location")
  section["places"] = []
  # TODO write function to create Place attribute pointer based on location string
  # Get places from Parse
  places = get_places()
  # Get location info from section (of form ["BRK 101", "TBA"])
  all_locations = section["location"].split(", ")
  # Filter out TBA
  # TODO Maybe do something else with them
  locations = [location for location in all_locations_unformatted if location != "TBA"]

  for location in locations:
    building_code = location.split(" ")[0]
    for place in places:
      if place["symbol"] == building_code:
        section["places"].append(place["id"])
        break;


  return section


places = []
def get_places():
  """
  Uses an HTTP GET to retrieve the Places data from Parse if not already retrieved
  """
  global pp_id, rest_api_key, places

  if not places:
    connection = httplib.HTTPSConnection('api.parse.com', 443)
    connection.connect()
    connection.request(
      'GET',
      '/1/classes/Place',
      {"X-Parse-Application-Id": app_id, "X-Parse-REST-API-Key": rest_api_key}
    )

  places = json.loads(connection.getresponse().read())
  return places

def put_child(course_id, section_id):
  """
  Given a Parse Course ID and Parse Section ID, adds the proper association (if it doesn't already exist) to 
  make the Parse Section one of the children of the Parse Course.
  """

  



def process_course(xml_course):
  """Entirely processes a Course given it's XML data. Creates / Updates the corresponding Parse Course and Parse Section."""
  parse_course = parse_get_course(xml_course)
  if not parse_course:  # Does not already exist, create
    parse_course = parse_create_course(xml_course)
  else:
    # TODO: Update existing attributes of the course here and upload the changes
    None
  parse_course_id = upload_course(parse_course)

  print ("Processed Course: {0} {1}"
    .format(parse_course["subject"], parse_course["courseNumber"]))

  # TODO: Implement the functions for this stuff
  # parse_section = parse_get_section(xml_course)
  # if not parse_section:  # Does not already exist, create
  #   parse_section = parse_create_section(xml_course)
  # else:
  #   # TODO: Update existing attributes of the section here and upload the changes
  #   None
  # parse_section_id = upload_section(parse_section)

  # put_child(parse_course_id, parse_section_id)





def main():
  """
  Note: the XML data queried in this script does not differentiate between courses and sections. For
  our purposes, we have two classes in Parse: Section, which represents a specific meeting of the class
  (with specific teacher, meeting schedule and location), and Course, which represents a course like PHYS 
  101 and all of the attributes that every section shares.
  """
  global pp_id, rest_api_key, term

  term = sys.argv[1]
  xml_filename = sys.argv[2]
  pp_id = sys.argv[3]
  rest_api_key = sys.argv[4]

  xml_courses = read_courses_tree(xml_filename)
  for i in range(5):
    # TODO: Process all courses once script is thoroughly tested
    process_course(xml_courses[i])
      


if __name__ == '__main__':
  main()