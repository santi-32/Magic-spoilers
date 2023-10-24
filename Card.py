import discord
class Card:
    
    def __init__(self, unparsedCard):
        self.front: dict
        self.back: dict
        Card.parseCard(self, unparsedCard)
        self.set = unparsedCard['set']
        self.set_name = unparsedCard['set_name']
        self.collector_number = unparsedCard['collector_number'] 
    
    def parseFace(self, unparsedFace, unparsedCard):
        face = dict()
        face['name'] = unparsedFace.get("name")
        face['types'] = unparsedFace.get("types")
        face['power'] = unparsedFace.get("power")
        face['toughness'] = unparsedFace.get("toughness")
        face['mana_cost'] = unparsedFace.get("mana_cost")
        face['oracle_text'] = unparsedFace.get("oracle_text")
        images = unparsedFace.get('image_uris')
        if images:
            face['image'] = images['png']
        face['_id'] = unparsedCard['id']
        face['set_name'] = unparsedCard['set_name']
        face['collector_number'] = unparsedCard['collector_number'] 
        return face

    def parseCard(self, unparsedCard):
        if "card_faces" in unparsedCard:
            unparsedFront = unparsedCard['card_faces'][0]
            unparsedBack = unparsedCard['card_faces'][1]
            self.modal = True
        else:
            unparsedFront = unparsedCard
            self.modal = False
        self.front = Card.parseFace(self, unparsedFront, unparsedCard)
        if self.modal:
            self.back = Card.parseFace(self, unparsedBack, unparsedCard)
            self.back['_id'] += '_2'
        
    def toMsg(self, face = 'front'):
        face = self.get(face)
        if face != None:
            pt = ''
            if (face.power != None and face.toughness != None):
                pt = ('\n' + face.power + '/' + face.toughness)
            Embed = discord.Embed(title=face.name, description=(str(face.mana_cost) + '\n' + str(face.types) + '\n' + str(face.text) + str(pt) + '\n' + '\n' + str(face.set_name)))
        if face.image != "No Image available":
            Embed.set_image(url=face.image)
        return Embed
    
    def toDict(self):
        if self.modal:
            return [self.front, self.back]
        else:
            return [self.front]
        

    

            
