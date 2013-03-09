'''
To do First::
- Release method for adding torrentReleases

To do after:
- add Subtitles list to Movie and connect with Releases
- Figure out where to put class comments

@author: ozbolt
'''

class Movie(object):
    '''
    ### Data ###
    AttributeName    AttTyp
    *obligatory 
    
    *title           String
    originalTitle    String
    *director        String
    *actors          {id, name}[]
    *genres          {int: String}[]
    *plot            String //Long
    *runTime         int
    *year            int
    
    *language        {int: String}
    country          {int: String}
       
    *id_IMDB         int
    id_FB            int
    id_RT            int
    id_Netflix       int
    id_Amazon        int
    
    *IMDB_rating     double
    *IMDB_votes      int
    *boxOffice       int
    rt_critics       int
    rt_audience      int
    
    *released        boolean
    *dateRelease     Date
    
    releasedSQ       boolean
    releasedHD       boolean
    releases         Release[]
    
    releasedNetflix  boolean
    releaseNetflix   Release
    
    releasedAmazon   boolean
    releaseAmazon    Release
    
    trailers         String
    *linkPhoto       String
    linkSite         String
    
    #Functions 
    
    '''
    
    def __init__(self, title = '', 
                 director = "", 
                 actors = {}, 
                 genres = {}, 
                 plot = "", 
                 runTime = -1, 
                 language = {},
                 id_IMDB = -1,
                 IMDB_rating = -1.0,
                 IMDB_votes = -1,
                 dateRelease = None,
                 linkPhoto = "",
                 year = -1,
                 boxOffice = 0):
        '''
        Constructor creates obligatory attributes
        '''
        self.title = title
        self.director = director
        self.actors = actors
        self.genres = genres
        self.plot = plot
        self.runTime = runTime
        self.language = language
        self.id_IMDB = id_IMDB
        self.IMDB_rating = IMDB_rating
        self.IMDB_votes = IMDB_votes
        self.dateRelease = dateRelease
        self.linkPhoto = linkPhoto
        self.year = year
        self.releases = []
        self.boxOffice = 0
        self.releases = []
        
    def hasRelease(self, rls):
        for r in self.releases:
            if r.data["rls"] == rls:
                return True
        return False
        
    def constructDict(self, additional = True):
        variables = ["title", "director", "actors", "year", "genres", "plot", "runTime", "language", "id_IMDB", "IMDB_rating", "IMDB_votes", "boxOffice", "dateRelease", "linkPhoto"]
        toRet = dict( (v, getattr(self, v)) for v in variables)
        if not additional:
            return toRet
        optVars = ["originalTitle", "id_RT", "id_FB", "id_Netflix", "id_Amazon", "rt_critics", "rt_audience", "releasedHD", "releasedSQ", "releases", "releasedNetflix", "releasedAmazon", "releaseNetflix", "releaseNetflix", "trailers", "linkSite"]
        for v in optVars:
            try:
                toRet[v] = getattr(self, v)
            except:
                pass
        
        return toRet
    
    def addTrailers(self, ts):
        if not ts:
            return
        
        for t in ts[0:-1]:
            self.addTrailer(t, sort=False)
        self.addTrailer(ts[-1])
    
    def addTrailer(self, t, sort = True):
        try:
            self.trailers.append(t)
        except:
            self.trailers = [t]
      
        if sort:
            self.trailers = sorted(self.trailers, key=lambda x: x["score"], reverse = True)
        
    def __str__(self):
        toRet = ""
        dct = self.constructDict()
        for k,v in dct.items():
            v = str(v)
            toRet += k +  " : " + v + "\n"
        return toRet
    
class Release(object):
    '''
    ### Data ###
    AttributeName    AttTyp 
    
    typ             int
    link            String
    releaseDate     Date
    data            {k:v}
    
    type:
        1 - SQ [500MB < rip < 1.6GB]
        2 - HD [1080p] [1GB < rip < 10GB]
        3 - Netflix
        4 - Amazon
        5 - LoveFilm
    
    data depends on release type.
        type{1,2}: 
         - size      int
         - seeds     int
         - peers     int
         - rls       String
         - hash      torrentzHash
        type{3, 5}:
         - HD        True/False
         - iw_ID     int #instawatcherID
         - expiresDate
        type{4}:
         - avaliable 1(Prime), 2(Rent), 3(Buy)
         - price     int
    '''

    def __init__(self, typ, link, releaseDate):
        self.typ = typ
        self.link = link
        self.releaseDate = releaseDate
        
    def __str__(self):
        variables = ["typ", "releaseDate", "link", "data"]
        dIct = dict( (v, getattr(self, v)) for v in variables)
        
        toRet = ""
        for k,v in dIct.items():
            v = str(v)
            toRet += k +  " : " + v + "\n"
            
        return toRet
    
