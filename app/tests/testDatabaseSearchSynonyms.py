#!/usr/bin/env python
# -*- coding: utf-8 -*-
#2020.0610 # Upgraded tests to v2; set up tests against AOP which seems to be discontinued and thus constant

import unittest
import requests

from unitTestConfig import base_plus_endpoint_encoded, headers

class TestDatabaseSearchSynonyms(unittest.TestCase):
    def test_search_fulltext_syn_1(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=body_xml%3A(hysteria)&synonyms=true')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        count1 = response_info["fullCount"]
        print (f"FullCount: {count1}")
        assert(count1 >= 90000 and count1 <= 110000)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=body_xml%3A(hysteria)&synonyms=false')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        print (r)
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        count1 = response_info["fullCount"]
        print (f"FullCount: {count1}")
        assert(count1 >= 6000 and count1 <= 6966)

    def test_search_fulltext_syn_2(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?title=("Freudian Metapsychology")&synonyms=false')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        count1 = response_info["fullCount"]
        print (f"FullCount: {count1}")
        assert(count1 >= 5 and count1 <= 10)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?title=("Freudian Metapsychology")&synonyms=true')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        count1 = response_info["fullCount"]
        print (f"FullCount: {count1}")
        assert(count1 >= 50 and count1 <= 60)

    def test_search_fulltext_syn_3(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=dreams_xml:(affect)&synonyms=false')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        count1 = response_info["fullCount"]
        print (f"FullCount: {count1}")
        assert(count1 >= 2 and count1 <= 10)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=dreams_xml:(affect)&synonyms=true')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        count1 = response_info["fullCount"]
        print (f"FullCount: {count1}")
        assert(count1 >= 60 and count1 <= 450)

    def test_search_fulltext_syn_4(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=dialogs_xml:(affect)&synonyms=false')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        count1 = response_info["fullCount"]
        print (f"FullCount: {count1}")
        assert(count1 >= 200 and count1 <= 210)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=dialogs_xml:(affect)&synonyms=true')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        count1 = response_info["fullCount"]
        print (f"FullCount: {count1}")
        assert(count1 >= 1560 and count1 <= 1600)

    def test_search_fulltext_syn_5(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=dialogs_xml:(affect)&synonyms=false')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        count1 = response_info["fullCount"]
        print (f"FullCount: {count1}")
        assert(count1 >= 200 and count1 <= 210)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=dialogs_xml:(affect)&synonyms=true')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        count1 = response_info["fullCount"]
        print (f"FullCount: {count1}")
        assert(count1 >= 1560 and count1 <= 1600)

    def test_search_fulltext_syn_6(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=quotes_xml:(bisexuality)&synonyms=false')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        count1 = response_info["fullCount"]
        print (f"FullCount: {count1}")
        assert(count1 >= 100 and count1 <= 110)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=quotes_xml:(bisexuality)&synonyms=true')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        count1 = response_info["fullCount"]
        print (f"FullCount: {count1}")
        assert(count1 >= 2122 and count1 <= 2222)

    def test_search_fulltext_syn_7(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=references_xml:(bisexuality)&synonyms=false')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        count1 = response_info["fullCount"]
        print (f"FullCount: {count1}")
        assert(count1 >= 560 and count1 <= 660)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=references_xml:(bisexuality)&synonyms=true')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        count1 = response_info["fullCount"]
        print (f"FullCount: {count1}")
        assert(count1 >= 8450 and count1 <= 8580)

    def test_search_fulltext_syn_8(self):
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=text:(externalization)&synonyms=false')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        count1 = response_info["fullCount"]
        print (f"FullCount: {count1}")
        assert(count1 >= 2300 and count1 <= 2400)
        full_URL = base_plus_endpoint_encoded('/v2/Database/Search/?fulltext1=text:(externalization)&synonyms=true')
        response = requests.get(full_URL, headers=headers)
        assert(response.ok == True)
        r = response.json()
        response_info = r["documentList"]["responseInfo"]
        response_set = r["documentList"]["responseSet"]
        count1 = response_info["fullCount"]
        print (f"FullCount: {count1}")
        assert(count1 >= 63000 and count1 <= 64000)

if __name__ == '__main__':
    unittest.main()
    
    
# Some samples of synonyms from our synonym table (Klemper's list)
 # abreaction	affect
 # abstinence	frustration
 # abstinence	neutrality
 # adaptation	ego
 # adolescence	ego
 # adolescence	masturbation
 # affect	abreaction
 # affect	depression
 # affect	discharge
 # affect	ego
 # affect	hate
 # affect	love
 # affect	isolation
 # affect	mood
 # affect	emotion
 # affect	anxiety
 # aggression	anger
 # aggression	conflict
 # aggression	death
 # aggression	defense
 # aggression	drive
 # aggression	energy
 # aggression	frustration
 # aggression	hate
 # aggression	id
 # aggression	neutralization
 # aggression	orality
 # aggression	sex
 # aggression	ambivalence
 # aggression	destructiveness
 # aggression	libido
 # aggression	masochism
 # aggression	rage
 # aggression	suicide
 # aggression	hostility
 # aggression	violence
 # aggression	sadism
 # ambivalence	depression
 # ambivalence	hate
 # ambivalence	love
 # ambivalence	aggression
 # ambivalence	conflict
 # amnesia	dissociation
 # amnesia	repression
 # amnesia	forgetting
 # amnesia	memory
 # anaclisis	object
 # anaclitic	depression
 # anal	libido
 # anality	character
 # anality	sadism
 # anger	aggression
 # anger	hostility
 # anxiety	ego
 # anxiety	fright
 # anxiety	guilt
 # anxiety	hysteria
 # anxiety	nightmare
 # anxiety	psychosis
 # anxiety	regression
 # anxiety	repression
 # anxiety	shame
 # anxiety	trauma
 # anxiety	unconscious
 # anxiety	conflict
 # anxiety	depression
 # anxiety	libido
 # anxiety	superego
 # anxiety	affect
 # anxiety	castration
 # anxiety	neurosis
 # anxiety	panic
 # anxiety	phobia
 # anxiety	fear
 # attention	conscious
 # autoerotism	narcissism
 # autoerotism	sexuality
 # autonomy	development
 # autonomy	ego
 # bereavement	death
 # bisexuality	perversion
 # bisexuality	transvestitism
 # bisexuality	homosexuality
 # bound	energy
 # castration	fantasy
 # castration	genitality
 # castration	anxiety
 # cathexes	economic
 # cathexis	ego
 # cathexis	energy
 # cathexis	libido
 # cathexis	object
 # censor	dream
 # censor	repression
 # censorship	condensation
 # censorship	repression
 # character	anality
 # character	hysteria
 # character	narcissism
 # character	normality
 # character	orality
 # character	neurosis
 # child	development
 # child	psychosis
 # child	infant
 # compromise	symptom
 # compulsion	obsession
 # condensation	censorship
 # condensation	displacement
 # condensation	dream
 # conflict	aggression
 # conflict	id
 # conflict	neurosis
 # conflict	somatization
 # conflict	superego
 # conflict	unconscious
 # conflict	ambivalence
 # conflict	anxiety
 # conflict	defense
 # conflict	ego
 # conscience	guilt
 # conscience	superego
 # conscious	attention
 # conscious	reality
 # conscious	resistance
 # conscious	unconscious
 # consciousness	perception
 # consciousness	preconscious
 # constitution	ego
 # conversion	somatization
 # conversion	hysteria
 # countertransference	resistance
 # countertransference	transference
 # curiosity	scopophilia
 # danger	anxiety
 # daydream	wish
 # daydreams	fantasy
 # death	aggression
 # death	bereavement
 # death	fantasy
 # death	mother
 # death	mourning
 # death	father
 # death	suicide
 # dedifferentiation	differentiation
 # dedifferentiation	regression
 # defence	neurosis
 # defence	repression
 # defense	aggression
 # defense	projection
 # defense	psychosis
 # defense	resistance
 # defense	conflict
 # defense	regression
 # delibidinization	aggression
 # delusion	hallucination
 # denial	fantasy
