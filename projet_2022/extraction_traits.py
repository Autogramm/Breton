import conll
import os
import sys
import re

def fromFolderToConllTrees(folder):

    liste_Trees=[]
    liste_rep=os.listdir(folder)
    for file in liste_rep:
        liste_Trees.append(conll.conllFile2trees(f"{folder}/{file}"))
    return liste_Trees

def dictGlossTag(liste_Trees):
    dict_Features={}
    for tree in liste_Trees:
        for sent in tree:
            for id in sent:
                for key in sent[id].keys():
                    if key!="gov" and key!="egov":
                        # print(key)
                        if "°" in str(sent[id][key]):
                            dict_Features[f"{key}_ambigu"]=dict_Features.get(f"{key}_ambigu",{})
                            dict_Features[f"{key}_ambigu"][sent[id][key]]=dict_Features[f"{key}_ambigu"].get(sent[id][key],0)+1
                            dict_Features[key]=dict_Features.get(key,{})
                            for tag in str(sent[id][key]).split("°"):
                                # print(tag)
                                dict_Features[key][tag]=dict_Features[key].get(tag,0)+1
                        else:
                            dict_Features[key]=dict_Features.get(key,{})
                            dict_Features[key][sent[id][key]]=dict_Features[key].get(sent[id][key],0)+1


    return dict_Features

if __name__=="__main__":
    folder=sys.argv[1]
    liste_Trees=fromFolderToConllTrees(folder)
    dict_Features=dictGlossTag(liste_Trees)
    print(dict_Features)
    
    for feat in dict_Features.keys():

        if len(dict_Features[feat])>2:
            f=open(f"autosheets/{feat}.tsv","w")
            f.write(f"fréquence\t{feat}\tUD\n")
            for value in dict_Features[feat].keys():
                f.write(f"{dict_Features[feat][value]}\t{value}\n")
            f.close