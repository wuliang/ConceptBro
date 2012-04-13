# -*- coding: utf8 -*-
import os
import sqlite3
import string
import exceptions

class ConceptSql:
    langs = ['cn', 'en',  'jp']
    def __init__(self, filename, primary, subary):
        if not os.path.exists(filename):
            raise exceptions.Exception("Database is not exist as %s" % filename)
        if primary:
          self.primary = primary
        else:
          self.primary = WikiNetSql.langs()
        self.subary = subary
        self.conn = sqlite3.connect(filename)
        if self.conn is None:
            raise exceptions.Exception("Database can't open from %s" % filename)
        #self.conn.text_factory = str
        
        self.primary_get_ids_of_word = []
        for lang in self.primary:
            if lang == 'cn':
                self.primary_get_ids_of_word.append(self.get_cn_ids_of_word)
            elif lang == 'en':
                self.primary_get_ids_of_word.append(self.get_en_ids_of_word)
            elif lang == 'jp':
                self.primary_get_ids_of_word.append(self.get_jp_ids_of_word)

        self.subary_get_ids_of_word = []
        for lang in self.subary:        
            if lang == 'cn':
                self.subary_get_ids_of_word.append(self.get_cn_ids_of_word)
            elif lang == 'en':
                self.subary_get_ids_of_word.append(self.get_en_ids_of_word)
            elif lang == 'jp':
                self.subary_get_ids_of_word.append(self.get_jp_ids_of_word)                

        self.primary_get_words_of_id = []
        for lang in self.primary:
            if lang == 'cn':
                self.primary_get_words_of_id.append(self.get_cn_words_of_id)
            elif lang == 'en':
                self.primary_get_words_of_id.append(self.get_en_words_of_id)
            elif lang == 'jp':
                self.primary_get_words_of_id.append(self.get_jp_words_of_id)   

        self.subary_get_words_of_id = []
        for lang in self.subary:        
            if lang == 'cn':
                self.subary_get_words_of_id.append(self.get_cn_words_of_id)
            elif lang == 'en':
                self.subary_get_words_of_id.append(self.get_en_words_of_id)
            elif lang == 'jp':
                self.subary_get_words_of_id.append(self.get_jp_words_of_id)  
                
    def commit(self):
        ret = self.conn.commit()
        return ret
        
    def close(self):
        
        self.conn.cursor().close()
        self.conn.close()
        
    def get_parsed_relations_of_id(self,  id):
        NotImplemented
                
    def get_definition_of_id(self, id):
        NotImplemented
                
    def get_cn_ids_of_word(self, word):
        NotImplemented

    def get_en_ids_of_word(self, word):
        NotImplemented
        
    def get_jp_ids_of_word(self, word):
        NotImplemented

    def get_all_ids_of_word(self,  word):
        result = []
        for func in self.primary_get_ids_of_word:
            result += func(word)
        if result:
            return result
            
        for func in self.subary_get_ids_of_word:
            result += func(word)
        return result
                
    def get_cn_words_of_id(self,  id):
        NotImplemented

    def get_en_words_of_id(self,  id):
        NotImplemented

    def get_jp_words_of_id(self,  id):
        NotImplemented
        
    def get_all_words_of_id(self,  id):        
        result = []
        for func in self.primary_get_words_of_id:
            result += func(id)
        if result:
            return result
            
        for func in self.subary_get_words_of_id:
            result += func(id)
        return result
            
class WikiNetSql(ConceptSql):
    
    def __init__(self, *args):
        ConceptSql.__init__(self, *args)
                
    def get_parsed_relations_of_id(self,  id):
        txts = self.get_raltions_of_id(id)
        full_txt = u" ".join(txts)
        relations = self.parse_realtions(full_txt)
        return relations
        
    def parse_realtions(self, txt):
        items = txt.split(" ")
        relations = {}
        rela = None
        for item in items:
            if len(item) == 0:
                continue
                
            if item[0] in string.digits:
                if rela is not None:
                    rela.append(int(item))
            else:
                rela = relations.setdefault(item, [])
        return relations
                
    def get_definition_of_id(self, id):
        c = self.conn.cursor()
        q = "SELECT definition FROM defs WHERE id = ? "
        rows = c.execute(q, (id, )).fetchall()
        return u" ".join([row[0] for row in rows])
                
    def get_cn_ids_of_word(self, word):
        c = self.conn.cursor()
        q = "SELECT id FROM words WHERE word = ? "
        rows = c.execute(q, (word, )).fetchall()
        return [row[0] for row in rows]

    def get_en_ids_of_word(self, word):
        c = self.conn.cursor()
        q = "SELECT id FROM enwords WHERE word = ? "
        rows = c.execute(q, (word, )).fetchall()
        return [row[0] for row in rows]

    def get_jp_ids_of_word(self, word):
        c = self.conn.cursor()
        q = "SELECT id FROM jpwords WHERE word = ? "
        rows = c.execute(q, (word, )).fetchall()
        return [row[0] for row in rows]
                
    def get_cn_words_of_id(self,  id):
        c = self.conn.cursor()
        q = "SELECT word FROM words WHERE id = ? "
        rows = c.execute(q, (id, )).fetchall()
        return [row[0] for row in rows]

    def get_en_words_of_id(self,  id):
        c = self.conn.cursor()
        q = "SELECT word FROM enwords WHERE id = ? "
        rows = c.execute(q, (id, )).fetchall()
        return [row[0] for row in rows]

    def get_jp_words_of_id(self,  id):
        c = self.conn.cursor()
        q = "SELECT word FROM jpwords WHERE id = ? "
        rows = c.execute(q, (id, )).fetchall()
        return [row[0] for row in rows]
                
    def get_raltions_of_id(self, id):        
        c = self.conn.cursor()
        q = "SELECT relation FROM relation WHERE id = ? "
        rows = c.execute(q, (id, )).fetchall()
        return [row[0] for row in rows]

class WordNetSql(ConceptSql):
    
    def __init__(self, *args):
        ConceptSql.__init__(self, *args)
        self.relations = {}
        for id,  name in self.get_definition_of_relation():
            self.relations[id] = name
        
    def get_definition_of_relation(self):
        c = self.conn.cursor()
        q = "SELECT linkid, name FROM linkdef"
        rows = c.execute(q, ()).fetchall()
        return rows

    def get_parsed_relations_of_id(self,  id):
        rows = self.get_raltions_of_id(id)
        relations = self.parse_realtions(rows)
        return relations
        
    def parse_realtions(self,  rows):
        relations = {}        
        for item, link in rows:
            rela = relations.setdefault(link, [])
            rela.append(item)
        relations1 = dict((self.relations[key], value) for (key, value) in relations.items())    
        return relations1
                  
    def get_definition_of_id(self, id):
        c = self.conn.cursor()
        q = "SELECT definition FROM synset WHERE synsetid = ? "
        rows = c.execute(q, (id, )).fetchall()
        return u" ".join([row[0] for row in rows])
                
    def get_cn_ids_of_word(self, word):
        # it has no CN word
        return []

    def get_en_ids_of_word(self, word):
        c = self.conn.cursor()
        q = "SELECT sense.synsetid FROM sense, word WHERE sense.wordid = word.wordid and word.lemma = ?"
        rows = c.execute(q, (word, )).fetchall()
        return [row[0] for row in rows]

    def get_jp_ids_of_word(self, word):
        # it has no JP word        
        return []
                
    def get_cn_words_of_id(self,  id):
        return []

    def get_en_words_of_id(self,  id):
        c = self.conn.cursor()
        q = "SELECT word.lemma FROM sense, word WHERE sense.wordid = word.wordid and sense.synsetid = ? "
        rows = c.execute(q, (id, )).fetchall()
        return [row[0] for row in rows]

    def get_jp_words_of_id(self,  id):
        return []
                
    def get_raltions_of_id(self, id):        
        c = self.conn.cursor()
        # first get semlinkref
        q = "SELECT synset2id, linkid FROM semlinkref WHERE synset1id = ? "
        rows = c.execute(q, (id, )).fetchall()
        return rows
        


def CreateConceptDB(dbConfig):
    dbtype = dbConfig['DBTYPE']
    filename = dbConfig['DBFILE']
    primary= dbConfig['LANG1']
    subary=dbConfig['LANG2']
    
    if dbtype not in ['wordnet',  'wikinet',  'jawordnet']:
        print "Unsupported Database type"
        return None
        
    if dbtype == 'wordnet':
        db = WordNetSql(filename,  primary,  subary)
        return db
    elif dbtype == 'wikinet':
        db = WikiNetSql(filename,  primary,  subary)
        return db
    elif dbtype == 'jawordnet': 
#        db = WikiNetSql(filename,  primary,  subary)
        return db

def main():
    wiki = CreateConceptDB(wikinet, "abcRelation.db")
    id = 12
    #relations = wiki.get_parsed_relations_of_id(id)
    #print relations
    words = wiki.get_all_words_of_id(id)   
    for word in words:
        print u'<'+ word
            
if __name__ == '__main__':
    main()
    
