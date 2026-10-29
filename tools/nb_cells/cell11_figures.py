# Research figures from actual temporal-test predictions.
figure_paths=[]
# ROC and PR curves
fig, axes = plt.subplots(1,2,figsize=(12,5))
plot_models = ['logistic_raw','xgboost_raw','logistic_ontology','xgboost_ontology','xgboost_ontology_no_ethnicity','xgboost_generic_control']
labels = {'logistic_raw':'Logistic raw','logistic_ontology':'Logistic + ontology features','xgboost_raw':'XGBoost raw',
          'xgboost_ontology':'XGBoost + ontology features','xgboost_ontology_no_ethnicity':'XGBoost + ontology (no ethnicity flag)',
          'xgboost_generic_control':'XGBoost + generic control'}
for name in plot_models:
    p=probabilities[name]
    fpr,tpr,_=roc_curve(y_test,p)
    prec,rec,_=precision_recall_curve(y_test,p)
    axes[0].plot(fpr,tpr,label=f"{labels[name]} (AUC {roc_auc_score(y_test,p):.3f})")
    axes[1].plot(rec,prec,label=f"{labels[name]} (AP {average_precision_score(y_test,p):.3f})")
axes[0].plot([0,1],[0,1],'--',color='gray',linewidth=1); axes[0].set_title('ROC curve — NHANES 2021–2023 temporal test'); axes[0].set_xlabel('False positive rate'); axes[0].set_ylabel('True positive rate')
axes[1].set_title('Precision–recall curve — NHANES 2021–2023 temporal test'); axes[1].set_xlabel('Recall'); axes[1].set_ylabel('Precision')
for ax in axes: ax.legend(fontsize=8); ax.grid(alpha=.25)
plt.tight_layout(); pth=ARTIFACT_DIR/'roc_pr_curves.png'; fig.savefig(pth,dpi=180,bbox_inches='tight'); figure_paths.append(str(pth)); plt.show()

# Calibration plot
fig,ax=plt.subplots(figsize=(6,5))
for name in plot_models:
    frac,mean_pred=calibration_curve(y_test,probabilities[name],n_bins=10,strategy='quantile')
    ax.plot(mean_pred,frac,marker='o',label=labels[name])
ax.plot([0,1],[0,1],'--',color='gray'); ax.set_xlabel('Mean predicted probability'); ax.set_ylabel('Observed positive fraction'); ax.set_title('Calibration on temporal test'); ax.legend(fontsize=8); ax.grid(alpha=.25)
plt.tight_layout(); pth=ARTIFACT_DIR/'calibration.png'; fig.savefig(pth,dpi=180,bbox_inches='tight'); figure_paths.append(str(pth)); plt.show()

# Fixed screening capacity sensitivity
fig,ax=plt.subplots(figsize=(9,5.5))
for policy,group in screening_budget_df.groupby('policy'):
    group=group.sort_values('capacity')
    ax.plot(group['capacity']*100,group['sensitivity'],marker='o',label=policy)
ax.plot([c*100 for c in CAPACITIES], [min(1.0, c/float(y_test.mean())) for c in CAPACITIES], 'k--', label='Capacity ceiling')
ax.set_xlabel('Screening capacity (% of eligible test cohort)'); ax.set_ylabel('Sensitivity / fraction of positive cases found'); ax.set_ylim(0,1); ax.set_title('Sensitivity at fixed screening capacity'); ax.legend(fontsize=7); ax.grid(alpha=.25)
plt.tight_layout(); pth=ARTIFACT_DIR/'capacity_sensitivity.png'; fig.savefig(pth,dpi=180,bbox_inches='tight'); figure_paths.append(str(pth)); plt.show()

# Primary effect interval
fig,ax=plt.subplots(figsize=(7,2.8))
ax.errorbar([primary_effect['difference']],[0],xerr=[[primary_effect['difference']-primary_effect['ci_low']],[primary_effect['ci_high']-primary_effect['difference']]],fmt='o',capsize=6)
ax.axvline(0,color='gray',linestyle='--'); ax.set_yticks([]); ax.set_xlabel('Hybrid minus ML-only sensitivity at 20% capacity'); ax.set_title('Paired bootstrap 95% interval (H2)'); ax.grid(axis='x',alpha=.25)
plt.tight_layout(); pth=ARTIFACT_DIR/'primary_effect_ci.png'; fig.savefig(pth,dpi=180,bbox_inches='tight'); figure_paths.append(str(pth)); plt.show()

# E1 learning curve
fig,axes=plt.subplots(1,2,figsize=(12,4.5))
for ax, metric, title in zip(axes, ['auprc_mean','sens_mean'], ['AUPRC on temporal test','Sensitivity at 20% capacity']):
    for family, style in [('logistic','-o'), ('xgboost','-s')]:
        for set_name, color in [('raw','#64748b'), ('ontology','#2563eb')]:
            sub = e1_summary[(e1_summary['model']==family) & (e1_summary['feature_set']==set_name)].sort_values('fraction')
            ax.plot(sub['fraction']*100, sub[metric], style, color=color, label=f'{family} {set_name}')
    ax.set_xlabel('Fraction of historical training data (%)'); ax.set_title(title); ax.grid(alpha=.25); ax.legend(fontsize=8)
plt.tight_layout(); pth=ARTIFACT_DIR/'e1_learning_curve.png'; fig.savefig(pth,dpi=180,bbox_inches='tight'); figure_paths.append(str(pth)); plt.show()

# E2 missing-input stress
fig,axes=plt.subplots(1,2,figsize=(12,4.5))
for name, label, style in [('logistic_raw','Logistic raw','--o'), ('logistic_ontology','Logistic + ontology','-o'),
                           ('xgboost_raw','XGBoost raw','--s'), ('xgboost_ontology','XGBoost + ontology','-s')]:
    sub = e2_summary[e2_summary['model']==name].sort_values('mask_rate')
    axes[0].plot(sub['mask_rate']*100, sub['auprc_mean'], style, label=label)
    axes[1].plot(sub['mask_rate']*100, sub['sens_mean'], style, label=label)
axes[0].set_xlabel('MCAR masking rate of selected inputs (%)'); axes[0].set_ylabel('AUPRC'); axes[0].set_title('E2 discrimination under missing inputs')
axes[1].set_xlabel('MCAR masking rate of selected inputs (%)'); axes[1].set_ylabel('Sensitivity at 20% capacity'); axes[1].set_title('E2 fixed-capacity screening under missing inputs')
for ax in axes: ax.grid(alpha=.25); ax.legend(fontsize=8)
plt.tight_layout(); pth=ARTIFACT_DIR/'e2_missing_input.png'; fig.savefig(pth,dpi=180,bbox_inches='tight'); figure_paths.append(str(pth)); plt.show()

# Model-family deltas (E3)
fig,ax=plt.subplots(figsize=(7,4))
names = list(paired_effects.keys())
point = [paired_effects[k]['difference'] for k in names]
low = [paired_effects[k]['ci_low'] for k in names]
high = [paired_effects[k]['ci_high'] for k in names]
ypos = np.arange(len(names))
ax.errorbar(point, ypos, xerr=[np.array(point)-np.array(low), np.array(high)-np.array(point)], fmt='o', capsize=4)
ax.axvline(0, color='gray', linestyle='--')
ax.set_yticks(ypos); ax.set_yticklabels([n.replace('_vs_raw','\nvs raw').replace('_ontology',' + ontology').replace('sens20','sens@20%') for n in names], fontsize=8)
ax.set_xlabel('Difference on the temporal test (95% paired bootstrap interval)'); ax.set_title('E3: effect of guideline features by model family')
ax.grid(axis='x', alpha=.25)
plt.tight_layout(); pth=ARTIFACT_DIR/'e3_model_family_deltas.png'; fig.savefig(pth,dpi=180,bbox_inches='tight'); figure_paths.append(str(pth)); plt.show()
