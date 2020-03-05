#
# National Parks Mycroft Skill
#

from adapt.intent import IntentBuilder

from mycroft.skills.core import MycroftSkill
from mycroft import intent_handler
from mycroft.skills.context import adds_context, removes_context
import requests
import random
import re

__author__ = 'richhowley'


# two letter codes are used by the API for 
# looking up parks by state
stateCodes =	{
  "alabama"     : "AL",
  "alaska"      : "AK",
  "arizona"     : "AZ",
  "arkansas"    : "AR",
  "california"  : "CA",
  "colorado"    : "CO",
  "connecticut" : "CT",
  "delaware"    : "DE",
  "district of columbia" : "DC",
  "washington dc"        : "DC",
  "dc"                   : "DC",
  "florida"     : "FL",
  "georgia"     : "GA",
  "hawaii"      : "HI",
  "idaho"       : "ID",
  "illinois"    : "IL",
  "indiana"     : "IN",
  "iowa"        : "IA",
  "kansas"      : "KS",
  "kentucky"    : "KY",
  "louisiana"   : "LA",
  "maine"       : "ME",
  "maryland"    : "MD",
  "massachusetts" : "MA",
  "michigan"    : "MI",
  "minnesota"   : "MN",
  "mississippi" : "MS",
  "missouri"    : "MO",
  "montana"     : "MT", 
  "nebraska"    : "NE",
  "nevada"      : "NV",
  "new hampshire" : "NH",
  "new jersey"    : "NJ",
  "new mexico"    : "NM",
  "new york"      : "NY",
  "north carolina": "NC",
  "north dakota"  : "ND",
  "ohio"          : "OH",
  "oklahoma"      : "OK",
  "oregon"        : "OR",
  "pennsylvania"  : "PA",
  "rhode island"  : "RI",
  "south carolina": "SC",
  "south dakota"  : "SD",
  "tennessee"     : "TN",
  "texas"         : "TX",
  "utah"          : "UT",
  "vermont"       : "VT",
  "virginia"      : "VA",
  "washington"    : "WA",
  "west virginia" : "WV",
  "wisconsin"     : "WI",
  "wyoming"       : "WY"  
}

# NPS class handles interaction with API
#
class NPS():
  
  def __init__(self, apiKey):
    
    # error flag valid after API is called
    self.serverError = False
    
    self.apiKey = apiKey;

  def initialize(self):
    pass
  
  # api key setter, called if settings chaned via web
  def setApiKey(self, key):
    
    self.apiKey = key


  # get data from NPS API at given endpoint with passed arguments
  def _getData(self,endPoint, args=None):

    retVal = None;
     
    # clear error flag
    self.serverError = False
     
    # format URL with end pint and API key
    api_url = "https://developer.nps.gov/api/v1/{}?&api_key={}".format(endPoint,self.apiKey)
    
    # add arguments if necessary
    if( args != None ):
      api_url = api_url + args
 
    try:
      
      # get requested data
      headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:62.0) Gecko/20100101 Firefox/62.0'}
      r = requests.get(api_url, headers=headers)
      
      # check if we got any data before setting return value
      retVal = r.json()['data'] if int(r.json()['total']) > 0 else None
      
    except:
      
      # set error flag
      self.serverError = True
    
    return retVal
     
  # check for api key before calling nps server
  def getData(self,endPoint, args=None):
  
    retVal = None;
    
    if self.apiKey == '':
      
      # set error flag
      self.serverError = True
      
    else:
   
      
      # we have an api key, try calling server
      retVal = self._getData(endPoint, args)
      
    return retVal
     
  # get passed string ready for speaking
  def cleanString(self, str):
      
    # some park names (e.g. in Alaska) use ampersands for "and"
    str = str.replace("&","and")
     
    # some park names (e.g.in Hawaii) have diacritical marks
    # remove them for lack of a better alternative
    str = re.sub('#[0-9]+;','',str)
           
    return str
      
  # API calls die silently, return true if last call
  # resulted in an error
  def callError(self):
    return self.serverError
 
  # trim imwaned entities from a list of parks 
  def trimParkList(self, parks):
  
    # remove trials and entities with no designation
    return  [park for park in parks if park['designation'] != '' and 'Trail' not in park['designation']]

          
  # return list of National Parks in state with passed name
  def getParksByState(self, state):
    nameList = []
    
    # look up code for passed state
    stateCode = stateCodes.get(state)
    if stateCode != None:
     
     # get all entries for state
     args = '&stateCode={}'.format(stateCode)
     parkList = self.getData('parks', args)
     
     if parkList != None:
      
      # remove trails from list
      parkList = self.trimParkList(parkList)
          
      # make list with just full names
      nameList = [self.cleanString(park['fullName']) for park in parkList]

    return nameList if len(nameList) > 0 else None
  
  
  
  # return data on park with passed name
  def getParkByName(self, parkName):
    
     retVal = None;
     
     # perform search with park name
     args = '&q={}'.format(parkName)
     parkList = self.getData('parks', args)
   
     if parkList != None:    
  
       # convert park name to lower case
       parkName = parkName.lower()
       
       # may have matched on any field,
       # look for park with passed name
       for park in parkList:

          # compare as lowercase
          if parkName in park['fullName'].lower():
            
            # clen name stering
            park['fullName'] = self.cleanString(park['fullName'])
            
            # return this park
            retVal = park
            break
 
     return retVal
  
  # format state names from state codes
  def formatStates(self, states):
    
      # make a list of state codes
      stateCodeList = states.split(',')
        
      # start with empty list of state names
      stateNameList = []
       
      # for each state code in park info 
      for stateCode in stateCodeList:
 
       # get each key from dictionary
       for key, scode in stateCodes.items():
        
        # if this key correspons to the state code, it's the state name 
        if scode == stateCode:
          stateNameList.append(key)
          break
 
      
      # insert 'and' before last state if there is more than one
      if len(stateNameList) > 1:
        stateNameList.insert(len(stateNameList)-1,'and')
        
      return stateNameList
              

  # return dictionary with park name, state string
  def getLocation(self, parkName):
  
    parkdata = None;

    # search API data for park
    park = self.getParkByName(parkName) 
      
    # if any park info was returned
    if park != None:
    
      # format list of state names
      stateNames = self.formatStates(park['states'])

      # format dictionary
      parkdata = {
        "location": ' '.join(stateNames),
        "park": park['fullName']

      }       
        

    return parkdata

  # return dictionary with location, park name
  # of randomly selected park
  def getQuizQuestion(self):
    
    parkdata = None;    
    
    # select a state
    keys = list(stateCodes.keys()) 
    stateIdx = random.randint(0, len(stateCodes)-1)
   
    # get all entries for state
    args = '&stateCode={}'.format(stateCodes.get(keys[stateIdx]))
    parkList = self.getData('parks', args)

    if parkList != None:
 
      # trim list to remove trails
      parkList = self.trimParkList(parkList)
               
      # select one park in state
      parkIdx = random.randint(0, len(parkList)-1)
          
      # format list of state names
      stateNames = self.formatStates(parkList[parkIdx]['states'])
         
      # format dictionary
      parkdata = {
        "location": ' '.join(stateNames),
        "park": parkList[parkIdx]['fullName']
    
      }
    
    # return park name and location
    return parkdata
 

  # return description of park with passed name
  def getDiscription(self, parkName):
    
    desc = ''
 
    # search API data for park
    park = self.getParkByName(parkName) 

    # if any park info was returned
    if park != None:
      
      # set return value to park description
      desc = self.cleanString(park['description'])  

    return desc if len(desc) > 0 else None


class NationalParksSkill(MycroftSkill):
  
    def __init__(self):
        super(NationalParksSkill, self).__init__(name="NationalParksSkill")
        self.quizQuestion = None
        
        # read NPS api key from settings and pass to constructor
        self.apiKey = self.settings.get('api_key')
        self.nps = NPS(self.apiKey)

        # watch for changes on HOME
        self.settings_change_callback = self.on_websettings_changed

    def on_websettings_changed(self):
      
      # try to read api key
      self.apiKey = self.settings.get('api_key')
      
      self.log.info('National Parks skill api set to ' + self.apiKey)
      
      # set key in NPS class
      self.nps.setApiKey(self.apiKey)

    # list the national parks in utah
    @intent_handler(IntentBuilder("ParkListIntent").require("List").
                    require("National.Parks").optionally("In").
                    require("Location").build())
    def handle_park_list_intent(self, message):
      
        # state spoken
        location =  message.data.get("Location")
        
        # ask api for list of parks in state
        parks = self.nps.getParksByState(location)
        
        # if we got a list of parks
        if parks != None:
        
          # format data for dialog
          parkdata = {
              "location": location,
              "parks" : ' '.join(parks)
          }
      
          self.speak_dialog("Park.List", parkdata )
          
        elif self.nps.callError():

          self.speak_dialog("Error.calling.server")
        
        else:
          
          parkdata = {'location' : location}        
          self.speak_dialog("No.Parks.Found.State", parkdata)
          
 
    # describe yellowstone national park
    @intent_handler(IntentBuilder("ParkDescriptionIntent").require("Describe").require("ParkName").require("National.Park").build())
    def handle_park_describe_intent(self, message):
      
      # pull park name from message
      requestedPark = message.data.get("ParkName")
     
      # get park description from NPS
      description = self.nps.getDiscription(requestedPark) 
      
      if description != None:
                
        self.speak(description)
        
      elif self.nps.callError():

        self.speak_dialog("Error.calling.server")
          
      else:
        parkdata = {'park' : requestedPark}
        self.speak_dialog("No.Parks.Found", parkdata)
    
    # where is yellowstone national park 
    @intent_handler(IntentBuilder("ParkLocationIntent").require("Whereis").require("ParkName").build())
    def handle_park_location_intent(self, message):

      # pull park name from message
      requestedPark = message.data.get("ParkName")
     
      # get park location from NPS
      parkdata = self.nps.getLocation(requestedPark)
    
      if parkdata != None:
        
        self.speak_dialog("Park.Location", parkdata)
        
      elif self.nps.callError():

        self.speak_dialog("Error.calling.server")
          
      else:
        parkdata = {'park' : requestedPark}
        self.speak_dialog("No.Parks.Found", parkdata)

    def stop(self):
      pass


    # quiz me on national parks
    @intent_handler(IntentBuilder("QuizIntent").require("Quiz.me").build())
    @adds_context('QuizContext')
    def handle_quiz_intent(self, message):
      
      # get qustion from nps class
      self.quizQuestion = self.nps.getQuizQuestion()
      
      # we either got a question or had a server error
      if self.quizQuestion != None:
      
        # ask question and wait for answer
        self.speak_dialog("Ask.Quiz.Question", self.quizQuestion, expect_response=True)
        
      else:
        
         self.speak_dialog("Error.calling.server")       

    @intent_handler(IntentBuilder('QuizAnswerIntent').require('QuizContext').build())
    @removes_context('QuizContext')
    def handle_quiz_answer_intent(self, message):
      
      # we are here due to quizcontext, get answer
      quizAnswer = (message.data.get('utterance'))
      
      # look for answer in question state list
      if quizAnswer in self.quizQuestion['location']:
        
        self.speak_dialog("Quiz.Question.Correct")
        
      else:
        
        self.speak_dialog("Quiz.Question.Wrong",self.quizQuestion)

    # repeat national parks quiz  
    @intent_handler(IntentBuilder("QuizRepeatIntent").require("Quiz.Repeat").build())
    def handle_quiz_repeat_intent(self, message):
      
      # if there is a question to repeat
      if self.quizQuestion != None:
          
        # set context so we can get an answer
        self.set_context('QuizContext')
        
        # ask question and wait for answer
        self.speak_dialog("Ask.Quiz.Question", self.quizQuestion, expect_response=True)
        
      else:
        
        # no preivous question
        self.speak_dialog("Quiz.Question.None", expect_response=False)
       
      
def create_skill():
    return NationalParksSkill()
