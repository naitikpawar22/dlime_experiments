import matplotlib.pyplot as plt
import numpy as np
from sklearn import preprocessing
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors

from explainer_tabular import LimeTabularExplainer
from load_dataset import LoadDataset

test = LoadDataset(which='hp')
X = test.data.data
feature_names = test.data.feature_names
target_names = test.data.target_names

#target_names = np.array(['Yes', 'No'])
#target_names = np.array(['normal', 'hyperthyroidism', 'hypothyroidism'])

train, test, labels_train, labels_test = train_test_split(test.data.data,
                                                          test.data.target,
                                                          train_size=0.80)

# train, test, labels_train, labels_test = train_test_split(preprocessing.scale(test.data.data),
#                                                           test.data.target,
#                                                           train_size=0.80)

# np.save("data/mc/X_train_hp.npy", train)
# np.save("data/mc/X_test_hp.npy", test)
# np.save("data/mc/y_train_hp.npy", labels_train)
# np.save("data/mc/y_test_hp.npy", labels_test)

# fix it
# train = np.load("data/synthetic/X_train_s6.npy")
# test = np.load("data/synthetic/X_test_s6.npy")
# labels_train = np.load("data/synthetic/y_train_s6.npy")
# labels_test = np.load("data/synthetic/y_test_s6.npy")

# train = preprocessing.scale(np.load("data/X_train_hp.npy"))
# test = preprocessing.scale(np.load("data/X_test_hp.npy"))
#
# labels_train = np.load("data/y_train_hp.npy")
# labels_test = np.load("data/y_test_hp.npy")

#rf = RandomForestClassifier(n_estimators=10, random_state=0, max_depth=5, max_features=5)
#rf.fit(train, labels_train)
#mean_accuracy = rf.score(test, labels_test)

lgr = LogisticRegression(max_iter = 1000, random_state=0).fit(train, labels_train)
mean_accuracy = lgr.score(test, labels_test)
e_true = lgr.coef_

explainer = LimeTabularExplainer(train,
                                 mode="classification",
                                 feature_names=feature_names,
                                 class_names=target_names,
                                 feature_selection="none",
                                 discretize_continuous=True,
                                 verbose=False)

clustering = AgglomerativeClustering(n_clusters=2).fit(X)
kmeans = KMeans(n_clusters=2).fit(X)
names = list(feature_names)+["membership"]
m_index = len(names) - 1
clustered_data = np.column_stack([X, clustering.labels_])
clustered_data_km = np.column_stack([X, kmeans.labels_])

nbrs = NearestNeighbors(n_neighbors=1, algorithm='ball_tree').fit(train)
distances, indices = nbrs.kneighbors(test)
clabel = clustering.labels_

def jaccard_similarity(list1, list2):
    s1 = set(list1)
    s2 = set(list2)
    return len(s1.intersection(s2)) / len(s1.union(s2))


def jaccard_distance(usecase):
    sim = []
    for l in usecase:
        i_sim = []
        for j in usecase:
            i_sim.append(1-jaccard_similarity(l, j))
        sim.append(i_sim)
    return sim

list_avg_cos_sim_dlime = []
list_avg_cos_sim_lime = []
list_avg_cos_sim_dlime_km = []
list_avg_cos_sim_dlime_tree = []

class_label_pred = lgr.predict(test)
class_label_prob = lgr.predict_proba(test)

g_x_lime = []
g_x_dlime = []

lst_fid_dlime = []
lst_fid_dlime_km = []
lst_fid_dlime_tree = []
lst_fid_lime = []

#local_preds_avg = np.zeros((test.shape[0],3), dtype=np.float32)

for x in range(0, test.shape[0]): #test.shape[0]
    use_case_one_features = []
    use_case_two_features = []
    use_case_three_features = []
    use_case_four_features = []
    dlime_list_coef = []
    dlime_km_list_coef = []
    dlime_tree_list_coef = []
    #dlime_list_coef_1 = []
    lime_list_coef = []
    #lime_list_coef_1 = []
    #subset = train[indices[x], :] # for NN

    lime_fid_list = []
    dlime_fid_list = []

    dlime_fid_list_km = []
    dlime_tree_fid_list = []

    #p_label = kmeans.predict([test[x]])
    p_label = clabel[indices[x]]
    N = clustered_data[clustered_data[:, m_index] == p_label[0]]
    subset = np.delete(N, m_index, axis=1)

    p_label_km = kmeans.predict([test[x]])
    #p_label = clabel[indices[x]]
    N_km = clustered_data_km[clustered_data_km[:, m_index] == p_label_km[0]]
    subset_km = np.delete(N_km, m_index, axis=1)

 ##   local_preds_iter = np.zeros((10,3), dtype=np.float32) # , dtype=np.float16

    for i in range(0, 10):

        ## DLIME
        exp_dlime, fid_dlime = explainer.explain_instance_hclust(test[x],
                                             lgr.predict_proba,
                                             num_features=test.shape[1],
                                             model_regressor=LinearRegression(),
                                             clustered_data = subset,
                                             regressor = 'linear',
                                             explainer='dlime',
                                             labels=(0, 1),
                                             ##labels=(0,1,2),
                                             ##labels=(0,1,2,3,4,4,5,6,7,8,9),
                                             blmodel = lgr,
                                             fidelity = True)

        exp_dlime_km, fid_dlime_km = explainer.explain_instance_hclust(test[x],
                                                                 lgr.predict_proba,
                                                                 num_features=test.shape[1],
                                                                 model_regressor=LinearRegression(),
                                                                 clustered_data=subset_km,
                                                                 regressor='linear',
                                                                 explainer='dlime',
                                                                 labels=(0,1),
                                                                 ##labels=(0,1,2),
                                                                 # labels=(0,1,2,3,4,4,5,6,7,8,9),
                                                                 blmodel=lgr,
                                                                 fidelity=True)


        ## DLIME-Tree
        exp_dlime_tree, fid_dlime_tree = explainer.explain_instance_hclust(test[x],
                                                                 lgr.predict_proba,
                                                                 num_features=test.shape[1],
                                                                 model_regressor="tree",
                                                                 clustered_data=subset,
                                                                 regressor='tree',
                                                                 explainer='dlime',
                                                                 labels=(0,1),
                                                                 ##labels=(0,1,2),
                                                                 # labels=(0,1,2,3,4,4,5,6,7,8,9),
                                                                 blmodel=lgr,
                                                                 fidelity=True)


        #fig_dlime, r_features = exp_dlime.as_pyplot_to_figure(type='h', name = i+.2, label='0')
        #fig_dlime.show()
        #use_case_two_features.append(r_features)
        dlime_list_coef.append(exp_dlime.easy_model_coef[0])
        dlime_km_list_coef.append(exp_dlime_km.easy_model_coef[0])
        dlime_tree_list_coef.append(exp_dlime_tree.easy_model_coef[0])
        #dlime_list_coef_0.append(exp_dlime.easy_model_coef[0])
        #dlime_list_coef_1.append(exp_dlime.easy_model_coef[1])

        dlime_fid_list.append(fid_dlime)
        dlime_fid_list_km.append(fid_dlime_km)
        dlime_tree_fid_list.append(fid_dlime_tree)

        #===================================================================================#

        exp_lime, fid_lime = explainer.explain_instance_hclust(test[x],
                                             lgr.predict_proba,
                                             num_features=test.shape[1],
                                             model_regressor= LinearRegression(),
                                             regressor = 'linear',
                                             explainer = 'lime',
                                             labels=(0,1),
                                             ##labels=(0,1,2),
                                             # labels=(0,1,2,3,4,4,5,6,7,8,9),
                                             num_samples=subset.shape[0],
                                             blmodel = lgr,
                                             fidelity = True)

        #fig_lime, r_features = exp_lime.as_pyplot_to_figure(type='h', name = i+.3, label='0')
        #fig_lime.show()
        #use_case_three_features.append(r_features)
        lime_list_coef.append(exp_lime.easy_model_coef[0])
        #lime_list_coef_0.append(exp_lime.easy_model_coef[0])
        #lime_list_coef_0.append(exp_lime.easy_model_coef[1])

        # for k, v in exp_dlime.local_pred.items():
        #     local_preds_iter[i, k] = v

        lime_fid_list.append(fid_lime)
        # local_p_lime = []
        # for k, v in exp_lime.local_pred.items():
        #     local_p_lime.append(v)

    ##local_preds_avg[x,: ] = np.mean(local_preds_iter, axis=0)

    lst_fid_dlime.append(sum(dlime_fid_list)/len(dlime_fid_list))
    lst_fid_dlime_km.append(sum(dlime_fid_list_km) / len(dlime_fid_list_km))
    lst_fid_dlime_tree.append(sum(dlime_tree_fid_list) / len(dlime_tree_fid_list))
    lst_fid_lime.append(sum(lime_fid_list)/len(lime_fid_list))

    ################################################
    # sim = jaccard_distance(use_case_two_features)
    # #np.savetxt("results/rf_dlime_jdist_bc.csv", sim, delimiter=",")
    # print(np.asarray(sim).mean())
    #
    # plt.matshow(sim);
    # plt.colorbar()
    # #plt.savefig("results/sim_use_case_2.pdf", bbox_inches='tight')
    # plt.show()

    ################################################
    # sim = jaccard_distance(use_case_three_features)
    # #np.savetxt("results/rf_lime_jdist_bc.csv", sim, delimiter=",")
    # print(np.asarray(sim).mean())
    #
    # plt.matshow(sim);
    # plt.colorbar()
    # #plt.savefig("results/sim_use_case_3.pdf", bbox_inches='tight')
    # plt.show()

    #e_pred_0 = exp_dlime.easy_model_coef[0]
    #e_pred_1 = exp_dlime.easy_model_coef[1]

    #ext_0 = np.expand_dims(e_pred_0, axis=0)
    #ext_1 = np.expand_dims(e_pred_1, axis=0)


    #cos_similarity_0 = cosine_similarity(e_true, ext_0)
    #cos_similarity_1 = cosine_similarity(e_true, ext_1)



    cos_similarity_dlime = abs(cosine_similarity(e_true, dlime_list_coef))
    cos_similarity_dlime_km = abs(cosine_similarity(e_true, dlime_km_list_coef))
    cos_similarity_dlime_tree = abs(cosine_similarity(e_true, dlime_tree_list_coef))
    cos_similarity_lime = abs(cosine_similarity(e_true, lime_list_coef))

    avg_cos_similarity_dlime = np.mean(cos_similarity_dlime)
    avg_cos_similarity_dlime_km = np.mean(cos_similarity_dlime_km)
    avg_cos_similarity_dlime_tree = np.mean(cos_similarity_dlime_tree)
    avg_cos_similarity_lime = np.mean(cos_similarity_lime)

    list_avg_cos_sim_dlime.append(avg_cos_similarity_dlime)
    list_avg_cos_sim_dlime_km.append(avg_cos_similarity_dlime_km)
    list_avg_cos_sim_dlime_tree.append(avg_cos_similarity_dlime_tree)
    list_avg_cos_sim_lime.append(avg_cos_similarity_lime)

    print(f"Actual Label = {labels_test[x]}")
    print(f"Cosine Similarity DLIME after 10 iterations = {avg_cos_similarity_dlime}")
    print(f"Cosine Similarity DLIME-KM after 10 iterations = {avg_cos_similarity_dlime_km}")
    print(f"Cosine Similarity DLIME-Tree after 10 iterations = {avg_cos_similarity_dlime_tree}")
    print(f"Cosine Similarity LIME after 10 iterations = {avg_cos_similarity_lime}")

    print(f"Fidelity DLIME after 10 iterations = {sum(dlime_fid_list)/len(dlime_fid_list)}")
    print(f"Fidelity DLIME-KM after 10 iterations = {sum(dlime_fid_list_km)/len(dlime_fid_list_km)}")
    print(f"Fidelity DLIME-Tree after 10 iterations = {sum(dlime_tree_fid_list)/len(dlime_tree_fid_list)}")
    print(f"Fidelity LIME after 10 iterations = {sum(lime_fid_list)/len(lime_fid_list)}")

print("================Overall Performance================")
o_avg_cos_similarity_dlime = np.mean(np.array(list_avg_cos_sim_dlime))
o_avg_cos_similarity_dlime_km = np.mean(np.array(list_avg_cos_sim_dlime_km))
o_avg_cos_similarity_dlime_tree = np.mean(np.array(list_avg_cos_sim_dlime_tree))
o_avg_cos_similarity_lime = np.mean(np.array(list_avg_cos_sim_lime))
print(f"Cosine Similarity DLIME Overall = {o_avg_cos_similarity_dlime}")
print(f"Cosine Similarity DLIME-KM Overall = {o_avg_cos_similarity_dlime_km}")
print(f"Cosine Similarity DLIME-Tree Overall = {o_avg_cos_similarity_dlime_tree}")
print(f"Cosine Similarity LIME Overall = {o_avg_cos_similarity_lime}")

avg_dlime_fid = sum(lst_fid_dlime)/len(lst_fid_dlime)
avg_dlime_fid_km = sum(lst_fid_dlime_km)/len(lst_fid_dlime_km)
avg_dlime_fid_tree = sum(lst_fid_dlime_tree)/len(lst_fid_dlime_tree)
avg_lime_fid = sum(lst_fid_lime)/len(lst_fid_lime)

print(f"Fidelity DLIME Overall = {avg_dlime_fid}")
print(f"Fidelity DLIME-KM Overall = {avg_dlime_fid_km}")
print(f"Fidelity DLIME-Tree Overall = {avg_dlime_fid_tree}")
print(f"Fidelity LIME Overall = {avg_lime_fid}")


#diff = np.subtract(class_label_prob, local_preds_avg)

print("Execution done")

