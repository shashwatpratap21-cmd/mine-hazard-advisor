import re, json, numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import accuracy_score, f1_score
df = pd.read_csv("accidents.csv")
def tidy(s):
    s = "" if pd.isna(s) else str(s)
    s = s.replace("“",'"').replace("”",'"').replace("’","'")
    return re.sub(r"\s+"," ",s).strip().strip('"').strip()
for c in ["situation","measures","measures_verbatim","search_text","cause_subgroup"]: df[c]=df[c].apply(tidy)
df["regulations"]=df["regulations"].fillna("None cited"); df["statutes_cited"]=df["statutes_cited"].fillna("None cited")
df["hazard"]=df["cause_group"].replace({"Transportation machinery (winding)":"Transportation machinery","Transportation machinery (non-winding)":"Transportation machinery"})
df=df[df["situation"].str.len()>=60].reset_index(drop=True)
kb=df[df["include_in_search_index"]==1].reset_index(drop=True)
train=df[df.year<=2020]; test=df[df.year>2020]
mk=lambda C=1: Pipeline([("tfidf",TfidfVectorizer(lowercase=True,ngram_range=(1,2),min_df=2,sublinear_tf=True,stop_words="english")),("clf",LogisticRegression(max_iter=3000,class_weight="balanced",C=C))])
grid=GridSearchCV(mk(),{"clf__C":[0.5,1,2,5,10,20]},cv=StratifiedKFold(5,shuffle=True,random_state=42),scoring="f1_macro",n_jobs=-1).fit(train.situation,train.hazard)
C=grid.best_params_["clf__C"]; p=grid.best_estimator_.predict(test.situation)
metrics=dict(C=C,test_acc=round(accuracy_score(test.hazard,p),3),test_f1=round(f1_score(test.hazard,p,average="macro"),3),
  baseline_acc=round(float((test.hazard==train.hazard.value_counts().index[0]).mean()),3),n_train=len(train),n_test=len(test),n_all=len(df),n_kb=len(kb))
print(metrics)
final=mk(C).fit(df.situation,df.hazard)
tf,lr=final.named_steps["tfidf"],final.named_steps["clf"]
vocab=tf.vocabulary_; inv=sorted(vocab,key=vocab.get)
clf_json=dict(terms=inv,idf=[round(float(x),4) for x in tf.idf_],classes=list(lr.classes_),
  coef=[[round(float(v),4) for v in row] for row in lr.coef_],intercept=[round(float(x),4) for x in lr.intercept_])
# retriever: TF-IDF fallback, exactly Embedder fallback
rv=TfidfVectorizer(ngram_range=(1,2),min_df=1,sublinear_tf=True,stop_words="english").fit(kb.search_text)
X=rv.transform(kb.search_text); X=X.multiply(1/ (np.sqrt(X.multiply(X).sum(1))+1e-12)).tocsr()
rinv=sorted(rv.vocabulary_,key=rv.vocabulary_.get)
docs=[]
for i in range(X.shape[0]):
    row=X.getrow(i); docs.append([row.indices.tolist(),[round(float(v),4) for v in row.data]])
ret_json=dict(terms=rinv,idf=[round(float(x),4) for x in rv.idf_],docs=docs)
cols=["id","year","date","mine_name","state","mineral","mine_type","place","hazard","cause_group","cause_subgroup","persons_killed","situation","measures","regulations","statutes_cited","source_document","source_page"]
recs=kb[cols].copy(); recs["persons_killed"]=recs.persons_killed.fillna(0).astype(int)
recs=recs.fillna("").astype(object)
out=dict(metrics=metrics,stop=sorted(ENGLISH_STOP_WORDS),clf=clf_json,ret=ret_json,kb=recs.values.tolist(),kbcols=cols,
  places=sorted(kb.place.dropna().unique().tolist()),mine_types=sorted(kb.mine_type.dropna().unique().tolist()))
s=json.dumps(out,separators=(",",":"),ensure_ascii=False)
open("model.json","w").write(s); print("MB",len(s)/1e6, len(inv), len(rinv))
# reference predictions for JS check
qs=["Drilling holes on a bench near an old blasted area in an opencast granite quarry","roof fall while installing supports at the face in underground coal mine"]
for q in qs:
    pr=final.predict_proba([q])[0]; qv=rv.transform([q]).toarray()[0]; qv/=np.linalg.norm(qv)+1e-12
    hz=final.predict([q])[0]; sims=X@qv + 0.1*(kb.hazard.values==hz)
    print(q[:30],hz,round(pr.max(),3),kb.id.values[np.argsort(-sims)[:6]].tolist())
