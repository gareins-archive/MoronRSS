'''
Created on Feb 13, 2013

@author: ozbolt
'''

from datetime import datetime

class Movie(object):
    '''
    ### Data ###
    AttributeName   AttTyp
    *obligatory
    
    *title           String
    originalTitle    String
    *director        String
    *actor           {int: String}[]
    *genre           {int: String}[]
    *plot            String //Long
    *runTime         int
    
    *language        {int: String}
    country          {int: String}
    *subtitle        {int: String}[] //int-languageID
       
    *id_IMDB         int
    id_FB            int
    id_RT            int
    id_Netflix       int
    id_Amazon        int
    
    *IMDB_rating     double
    *IMDB_votes      int
    
    *dateRelease     Date
    dateDVDrip       Date
    dateHDrip        Date
    dateNetflix      Date
    dateAmazon       Date
    
    linkTrailer      String
    linkDVDrip       String
    linkHDrip        String
    linkNetflix      String
    linkAmazon       String
    *linkPhoto       String
    linkSite         String
    
    #Functions 
    
    '''
    
    def __init__(self, title = '', 
                 director = "", 
                 actor = {}, 
                 genre = {}, 
                 plot = "", 
                 runTime = -1, 
                 language = {}, 
                 subtitle = {},
                 id_IMDB = -1,
                 IMDB_rating = -1.0,
                 IMDB_votes = -1,
                 dateRelease = datetime(1970,1,1),
                 linkPhoto = "" ):
        '''
        Constructor creates obligatory attributes
        '''
        self.title = title
        self.director = director
        self.actor = actor
        self.genre = genre
        self.plot = plot
        self.runTime = runTime
        self.language = language
        self.subtitle = subtitle
        self.id_IMDB = id_IMDB
        self.IMDB_rating = IMDB_rating
        self.IMDB_votes = IMDB_votes
        self.dateRelease = dateRelease
        self.linkPhoto = linkPhoto
    
    def addAtributes(self, data):
        for at in self.attributes:
            if at in data:
                print(at, ":", data[at])
                self.allD[at] = data[at]
            else:
                print("Error: attribute ", at, " not found")
                #raise 
        for at in self.attributesOther:
            if at in data:
                print(at, " : ", data[at])
                self.allD[at] = data[at]

class Base:
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        
    def creatBase(self):
        print(")")
      
      
if __name__ == "__main__":    
    a = Movie()
    
    data = {'title': 'La vita e bella', 'director': {1: "Roberto Benigni", 7: "Rod Dean"}, "id_FB" : 12345}
    a.addAtributes(data)  
