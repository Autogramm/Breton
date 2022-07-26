import conll, re, sys, os
from pathlib import Path
import spacy

nlp=spacy.load("fr_core_news_md")

def folder2ConllTrees(folder):
    """
    input : a folder of conll files
    output : a dictionnary, the keys will be the files names', and the value for each key is a list of conll Trees
    """
    conlldict={}
    files_l=os.listdir(folder)
    for file in files_l:
        path = Path(f"{folder}/{file}")
        if path.is_file():
            conll_Tree=conll.conllFile2trees(path)
            conlldict[file]=conll_Tree
    return conlldict

def makeRegExFromDictKeys(dict):
    """
    input : a dictionnary, the keys must be the different affixes the regex should look for
    output : a compiled RegEx of every affix like so (affix1$|affix2$...)
    The use of a dictionnary isn't absolutely necessary for this process, but it allows to use
    the same dictionnary in the function responsible for adding the Gloss based on these suffixes
    making it so that you only need to modify one variable if needed.
    """
    string=""
    for key in dict.keys():
        if string:
            string=f"{string}|{key}$"
        else:
            string=f"{key}$"
    
    string=f"({string})"
    return re.compile(string)

def tokenType(conll_Tree,i,sent,id):
    """
    input : a conll_Tree Object, the index of a sentence in this tree, the id of a token
    output : will add the feature "TokenType=Aff" if there's a "-" in the text
        or "TokenType=Clit" if there's a "="
    """
    if re.search(r"\-",sent[id]['t']):
        conll_Tree[i][id]["TokenType"]="Aff"
    elif re.search(r"=",sent[id]['t']):
        conll_Tree[i][id]["TokenType"]="Clit"    
    return True

def createCorrespondanceDictFromFolder(folder):
    correspondanceDict={}
    for file in os.listdir(folder):
        correspondanceDict[file.split(".")[0]]=createCorrespondanceDictFromFile(f"{folder}/{file}")
    return correspondanceDict

def createCorrespondanceDictFromFile(file):
    """
    input : a csv file having three columns "fréquence, Gloss, UD" the Gloss column containing 
        a possible gloss for a token, the fréquence column showing the number of times it is used and
        the UD columns giving a UD correspondance of what can be understood from the Gloss
    output : a dictionnary having the content of the Gloss column as keys and the content of the UD column
        as values
    """
    correspondanceDict={}
    regList=re.compile(r".+?\t(.+?)\t([^\n\t]+)")
    with open(file,"r",encoding="UTF-8") as f:
        f.readline()
        line=f.readline()
        while line:
            if re.match(regList,line):
                m=re.match(regList,line)
                list_feat_value=[(x.split("=")[0],x.split("=")[1]) for x in m.group(2).split("|")]
                i=0
                while i<len(list_feat_value):
                    if list_feat_value[i][0]=="upos":
                        list_feat_value[i]=("tag",list_feat_value[i][1])
                    i+=1
                correspondanceDict[m.group(1).strip("[] ")]=list_feat_value
            line=f.readline()
    return correspondanceDict

def addFromCorrespondanceFile(conll_Tree,i,sent,id,corresDict):
    """
    input : a conll_Tree, the index of a sentence, a sentence Tree from the conll_Tree, the id of a token and 
        a dictionnary created using createCorrespondanceDictFromFile
    output : will add the UD correspondances from the dictionnary to the conll_Tree
    """
    ordre=["lemma","Gloss","tag","t"]
    for feature in ordre:
        values=sent[id][feature].split(".")
        for value in values:
            if corresDict[feature].get(value,False):
                for f,v in corresDict[feature][value]:
                    conll_Tree[i][id][f]=v
    return True

def ifEqualOrDashInTextEqualInGloss(conll_Tree,sent,i,id):
    """
    input : a conll_Tree, the index of a sentence, a sentence Tree from the conll_Tree, the id of a token
    output : if there is a "=" or a "-" in the text, it is added to the Gloss
    """
    #If the equal or dash is in the Gloss but not in the text
    if re.match(r"(\-|=).+",sent[id]['Gloss']) and not re.match(r"(\-|=).+",sent[id]['t']):
        m=re.match(r"(\-|=).+",sent[id]['Gloss'])
        eq=m.group(1)
        conll_Tree[i][id]['t']=f"{eq}{conll_Tree[i][id]['t']}"
    elif re.match(r".+(\-|=)",sent[id]['Gloss']) and not re.match(r".+(\-|=)",sent[id]['t']):
        m=re.match(r".+(\-|=)",sent[id]['Gloss'])
        eq=m.group(1)
        conll_Tree[i][id]['t']=f"{conll_Tree[i][id]['t']}{eq}"

    #If the equal or dash is in the text but not in the gloss
    if re.match(r"(\-|=).+",sent[id]['t']) and not re.match(r"(\-|=).+",sent[id]['Gloss']):
        m=re.match(r"(\-|=).+",sent[id]['t'])
        eq=m.group(1)
        conll_Tree[i][id]['Gloss']=f"{eq}{conll_Tree[i][id]['Gloss']}"
    elif re.match(r".+(\-|=)",sent[id]['t']) and not re.match(r".+(\-|=)",sent[id]['Gloss']):
        m=re.match(r".+(\-|=)",sent[id]['t'])
        eq=m.group(1)
        conll_Tree[i][id]['Gloss']=f"{conll_Tree[i][id]['Gloss']}{eq}"

def pleaseSpacyGiveMeSomeTags(conll_Tree,sent,i,id,nlp):
    """
    Input : a conll_Tree, the index of a sentence, a sentence Tree from the conll_Tree, the id of a token, 
        a nlp parsing function made using spacy
    Output : adds tags to a conll based on the tags the parser would give to the gloss
    """
    if sent[id]['tag']=="_" and re.match(r"[a-z]+$",sent[id]['Gloss']):
        token=nlp(sent[id]['Gloss'].strip("-"))
        for tok in token:
            if tok.pos_!='ADJ' or re.match(r"(masu?|toli|mawuti?|lebata|tuara?|n wae|valu)",sent[id]['lemma']):
                conll_Tree[i][id]['tag']=tok.pos_
            else:
                conll_Tree[i][id]['tag']="VERB|ATTRIBUTIF"

def uposToExtPos(conll_Tree,i,id):
    if not conll_Tree[i][id].get('ExtPos',False):
        conll_Tree[i][id]['ExtPos']=conll_Tree[i][id]['tag']
    return True

def pleaseSpacyGiveMeSomeMorphology(conll_Tree,sent,i,id,nlp):
    g=sent[id]['Gloss']
    if re.search(r"[^ \t\n]",g):
        doc=nlp(g)
        token=doc[0]
        if token.pos_=="VERB":
            for feature_value in token.morph:
                feature_value=feature_value.split("=")
                feature=feature_value[0]
                value=feature_value[1]
                conll_Tree[i][id][feature]=value
    return True

def correction_conllTree(conll_Tree,correspondanceDict):
    """
    Input : a conll_Tree object, a correspondanceDict made using createCorrespondanceDictFromFile
    Output : a number of corrections and additions to the conll_Tree 
    """

    for i, sent in enumerate(conll_Tree):
        


        for id in sent.keys():
            uposToExtPos(conll_Tree,i,id)

            addFromCorrespondanceFile(conll_Tree,i,sent,id,correspondanceDict)

            ifEqualOrDashInTextEqualInGloss(conll_Tree,sent,i,id)

            tokenType(conll_Tree,i,sent,id)

            if re.match(r".*[^A-Z].*",conll_Tree[i][id]['tag']):

                pleaseSpacyGiveMeSomeMorphology(conll_Tree,sent,i,id,nlp)
                
            if re.match(r".*[^A-Z].*",conll_Tree[i][id]['tag']):

                pleaseSpacyGiveMeSomeTags(conll_Tree,sent,i,id,nlp)

                


    return conll_Tree

def correction_Folder(folder,correspondanceDict):
    """
    input : A folder, a correspondanceDict made using createCorrespondanceDictFromFile
    output : a dictionnary of the modified trees, using the filename as key
    """
    conlldict=folder2ConllTrees(folder)
    correctedTrees={}

    for file in conlldict.keys():
        correctedTree=correction_conllTree(conlldict[file],correspondanceDict)
        correctedTrees[file]=(correctedTree)

    return correctedTrees

def rewriteCorrectedFiles(correctedTrees,outputFolder="corrected/"):
    """
    input : A dictionnary created using correction_Folder, an output folder
    outut : the rewriting of the corrected trees in the new folder
    """
    path=Path(outputFolder)
    if not path.is_dir():
        os.makedirs(outputFolder)
    for file in correctedTrees.keys():
        conll.trees2conllFile(correctedTrees[file], f"{outputFolder}/{file}")
    return True

def fromConllFolder2CorrectedConllFolder(folder,correspondanceDict,output="corrected/"):
    """
    input : a folder of conll files, a correspondanceDict made using createCorrespondanceDictFromFile and an output folder
    output : A new folder containing modified conll files, these will need post processing using another script
    """
    correctedTrees=correction_Folder(folder,correspondanceDict)
    rewriteCorrectedFiles(correctedTrees, output)
    return True

if __name__ == "__main__":

    folder=sys.argv[1]
    correspondanceFolder=sys.argv[2]
    correspondanceDict=createCorrespondanceDictFromFolder(correspondanceFolder)
    fromConllFolder2CorrectedConllFolder(folder,correspondanceDict)