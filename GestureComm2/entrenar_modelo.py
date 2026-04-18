# ============================================================
#  entrenar_modelo.py  —  Entrena y evalúa el modelo completo
# ============================================================
"""
Genera en models/:
  modelo_gestos.h5          — modelo TF/Keras listo
  etiquetas.npy             — lista de clases
  curvas_entrenamiento.png  — accuracy + loss por época
  matriz_confusion.png      — confusión (conteo + normalizada)
  reporte_clasificacion.png — precision / recall / f1 por gesto
  arquitectura_red.png      — diagrama de la red neuronal
  dashboard_evaluacion.png  — resumen ejecutivo

USO: python entrenar_modelo.py
"""
import os, numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing   import LabelEncoder
from sklearn.metrics         import (confusion_matrix, classification_report,
                                     precision_score, recall_score, f1_score)
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, callbacks

from config import (DATASET_FILE, MODEL_FILE, LABEL_FILE, MODELS_DIR,
                    FEATURE_SIZE, EPOCHS, BATCH_SIZE, VALIDATION_SPLIT,
                    LEARNING_RATE, DROPOUT_RATE)

tf.random.set_seed(42); np.random.seed(42)

# ── Paleta de colores ─────────────────────────────────────────
BG=    '#0D1117'; SURFACE='#161B22'; CARD=  '#1C2128'; BORDER='#30363D'
CYAN=  '#00D4AA'; ORANGE= '#FF6B35'; GREEN= '#3FB950'; RED=   '#F85149'
YELLOW='#D29922'; TEXT=   '#E6EDF3'; MUTED= '#8B949E'

def apply_dark_style():
    plt.rcParams.update({
        'figure.facecolor':BG,'axes.facecolor':CARD,'axes.edgecolor':BORDER,
        'axes.labelcolor':TEXT,'xtick.color':MUTED,'ytick.color':MUTED,
        'text.color':TEXT,'grid.color':BORDER,'grid.linestyle':'--',
        'grid.alpha':0.5,'font.family':'DejaVu Sans','font.size':11,
    })

# ══════════════════════════════════════════════════════════════
#  1. DATOS
# ══════════════════════════════════════════════════════════════
def cargar_dataset():
    if not os.path.exists(DATASET_FILE):
        print(f'\n  ✗ Dataset no encontrado: {DATASET_FILE}')
        print('    Ejecuta primero: python crear_dataset.py\n'); exit(1)
    df = pd.read_csv(DATASET_FILE)
    print(f'\n{"═"*54}\n  DATASET: {len(df)} muestras\n{"═"*54}')
    for g,n in df['gesto'].value_counts().items():
        ok='✓' if n>=50 else '!'
        print(f'  {ok} {g:12s} {n:4d}  {"█"*(n//5)}')
    print(f'{"═"*54}\n')
    return df

def preprocesar(df):
    X  = df.iloc[:,:FEATURE_SIZE].values.astype(np.float32)
    le = LabelEncoder()
    y  = le.fit_transform(df['gesto'].values)
    yc = keras.utils.to_categorical(y, len(le.classes_))
    X_tr,X_v,y_tr,y_v = train_test_split(
        X,yc,test_size=VALIDATION_SPLIT,random_state=42,stratify=y)
    print(f'  Train: {len(X_tr)}  |  Val: {len(X_v)}')
    print(f'  Clases ({len(le.classes_)}): {list(le.classes_)}\n')
    return X_tr,X_v,y_tr,y_v,le

# ══════════════════════════════════════════════════════════════
#  2. MODELO
# ══════════════════════════════════════════════════════════════
def construir_modelo(n):
    m = keras.Sequential([
        layers.Input(shape=(FEATURE_SIZE,), name='input_landmarks'),
        layers.Dense(128, name='d1'), layers.BatchNormalization(),
        layers.Activation('relu'), layers.Dropout(DROPOUT_RATE),
        layers.Dense(64,  name='d2'), layers.BatchNormalization(),
        layers.Activation('relu'), layers.Dropout(DROPOUT_RATE),
        layers.Dense(32,  name='d3'), layers.BatchNormalization(),
        layers.Activation('relu'), layers.Dropout(DROPOUT_RATE/2),
        layers.Dense(n, activation='softmax', name='output'),
    ], name='modelo_gestos')
    m.compile(optimizer=keras.optimizers.Adam(LEARNING_RATE),
              loss='categorical_crossentropy', metrics=['accuracy'])
    m.summary(); return m

def entrenar(m, X_tr, X_v, y_tr, y_v):
    cbs = [
        callbacks.ModelCheckpoint(MODEL_FILE, save_best_only=True,
                                  monitor='val_accuracy', verbose=1),
        callbacks.EarlyStopping(monitor='val_accuracy', patience=20,
                                restore_best_weights=True, verbose=1),
        callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5,
                                    patience=10, min_lr=1e-6, verbose=1),
    ]
    return m.fit(X_tr,y_tr, validation_data=(X_v,y_v),
                 epochs=EPOCHS, batch_size=BATCH_SIZE,
                 callbacks=cbs, verbose=1)

# ══════════════════════════════════════════════════════════════
#  3. GRÁFICAS
# ══════════════════════════════════════════════════════════════
def grafica_curvas(history):
    apply_dark_style()
    acc     = history.history['accuracy']
    val_acc = history.history['val_accuracy']
    loss    = history.history['loss']
    val_loss= history.history['val_loss']
    ep = range(1, len(acc)+1)

    fig = plt.figure(figsize=(18,9), facecolor=BG)
    fig.suptitle('Entrenamiento de la Red Neuronal — Sistema de Gestos',
                 color=TEXT, fontsize=16, fontweight='bold', y=0.97)
    gs = gridspec.GridSpec(2,3,figure=fig,hspace=0.42,wspace=0.35,
                           left=0.06,right=0.97,top=0.90,bottom=0.08)

    # Accuracy
    ax1=fig.add_subplot(gs[0,:2]); ax1.set_facecolor(CARD)
    for sp in ax1.spines.values(): sp.set_edgecolor(BORDER)
    ax1.plot(ep,acc,     color=CYAN,  lw=2.2,label='Train Accuracy')
    ax1.plot(ep,val_acc, color=ORANGE,lw=2.2,label='Val Accuracy',linestyle='--')
    ax1.fill_between(ep,acc,val_acc,alpha=0.07,color=ORANGE)
    best=int(np.argmax(val_acc))
    ax1.axvline(best+1,color=GREEN,lw=1.2,linestyle=':',alpha=0.7)
    ax1.annotate(f' Best {best+1}\n {val_acc[best]:.3f}',
        xy=(best+1,val_acc[best]),xytext=(best+6,val_acc[best]-0.08),
        color=GREEN,fontsize=9,arrowprops=dict(arrowstyle='->',color=GREEN,lw=1.2))
    ax1.axhspan(0.85,1.02,alpha=0.04,color=GREEN)
    ax1.set_ylim(0.2,1.02); ax1.set_title('Exactitud (Accuracy)',color=TEXT,fontsize=12,fontweight='bold')
    ax1.set_xlabel('Época',color=MUTED,fontsize=10); ax1.set_ylabel('Accuracy',color=MUTED,fontsize=10)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f'{v:.0%}'))
    ax1.legend(facecolor=SURFACE,edgecolor=BORDER,labelcolor=TEXT,fontsize=10); ax1.grid(True)

    # Loss
    ax2=fig.add_subplot(gs[1,:2]); ax2.set_facecolor(CARD)
    for sp in ax2.spines.values(): sp.set_edgecolor(BORDER)
    ax2.plot(ep,loss,     color=CYAN,lw=2.2,label='Train Loss')
    ax2.plot(ep,val_loss, color=RED, lw=2.2,label='Val Loss',linestyle='--')
    ax2.fill_between(ep,loss,val_loss,alpha=0.07,color=RED)
    ax2.set_title('Pérdida (Loss)',color=TEXT,fontsize=12,fontweight='bold')
    ax2.set_xlabel('Época',color=MUTED,fontsize=10); ax2.set_ylabel('Categorical Crossentropy',color=MUTED,fontsize=10)
    ax2.legend(facecolor=SURFACE,edgecolor=BORDER,labelcolor=TEXT,fontsize=10); ax2.grid(True)

    # Panel métricas
    ax3=fig.add_subplot(gs[:,2]); ax3.set_facecolor(SURFACE); ax3.axis('off')
    ax3.set_title('Métricas Finales',color=TEXT,fontsize=12,fontweight='bold',pad=12)
    items=[
        ('Train Accuracy',f'{acc[-1]*100:.2f}%',CYAN),
        ('Val Accuracy',  f'{val_acc[-1]*100:.2f}%',ORANGE),
        ('Train Loss',    f'{loss[-1]:.4f}',CYAN),
        ('Val Loss',      f'{val_loss[-1]:.4f}',RED),
        ('Best Val Acc',  f'{max(val_acc)*100:.2f}%',GREEN),
        ('Best Epoch',    f'{int(np.argmax(val_acc))+1}',GREEN),
        ('Total Épocas',  f'{len(acc)}',MUTED),
        ('Clases',        '9',MUTED),
        ('Input Features','63',MUTED),
        ('Arquitectura',  '128→64→32→9',YELLOW),
    ]
    for i,(lbl,val,col) in enumerate(items):
        y=0.88-i*0.086
        ax3.add_patch(FancyBboxPatch((0.03,y-0.032),0.94,0.065,
            boxstyle='round,pad=0.01',facecolor=CARD,edgecolor=BORDER,lw=0.8,transform=ax3.transAxes))
        ax3.text(0.08,y,lbl,transform=ax3.transAxes,color=MUTED,fontsize=9,va='center')
        ax3.text(0.97,y,val,transform=ax3.transAxes,color=col,fontsize=10,fontweight='bold',va='center',ha='right')

    plt.savefig(os.path.join(MODELS_DIR,'curvas_entrenamiento.png'),dpi=150,bbox_inches='tight',facecolor=BG)
    plt.close(); print('  ✓ curvas_entrenamiento.png')


def grafica_confusion(y_true, y_pred, clases):
    apply_dark_style()
    labels = [c.capitalize() for c in clases]
    cm     = confusion_matrix(y_true, y_pred)
    cm_n   = cm.astype(float)/cm.sum(axis=1)[:,None]

    fig,axes=plt.subplots(1,2,figsize=(18,8),facecolor=BG)
    fig.suptitle('Análisis de Clasificación — Matriz de Confusión',
                 color=TEXT,fontsize=15,fontweight='bold',y=0.97)

    for ax,data,fmt,cmap,tit in [
        (axes[0],cm,'d','YlOrRd','Conteo de Predicciones'),
        (axes[1],cm_n,'.2f','Blues','Normalizada por Clase'),
    ]:
        ax.set_facecolor(CARD)
        sns.heatmap(data,annot=True,fmt=fmt,ax=ax,cmap=cmap,
                    xticklabels=labels,yticklabels=labels,
                    linewidths=0.5,linecolor=BORDER,
                    annot_kws={'size':10,'fontweight':'bold'},
                    cbar_kws={'shrink':0.8})
        ax.set_title(tit,color=TEXT,fontsize=13,pad=10,fontweight='bold')
        ax.set_xlabel('Predicho',color=MUTED,fontsize=11)
        ax.set_ylabel('Real',color=MUTED,fontsize=11)
        ax.tick_params(colors=TEXT,labelsize=10)
        ax.set_xticklabels(ax.get_xticklabels(),rotation=35,ha='right',color=TEXT)
        ax.set_yticklabels(ax.get_yticklabels(),rotation=0,color=TEXT)
        plt.setp(ax.collections[0].colorbar.ax.yaxis.get_ticklabels(),color=MUTED)

    plt.tight_layout(rect=[0,0,1,0.95])
    plt.savefig(os.path.join(MODELS_DIR,'matriz_confusion.png'),dpi=150,bbox_inches='tight',facecolor=BG)
    plt.close(); print('  ✓ matriz_confusion.png')


def grafica_reporte(y_true, y_pred, clases):
    apply_dark_style()
    labels = [c.capitalize() for c in clases]
    pre = precision_score(y_true,y_pred,average=None,zero_division=0)
    rec = recall_score(y_true,y_pred,average=None,zero_division=0)
    f1  = f1_score(y_true,y_pred,average=None,zero_division=0)

    fig,ax=plt.subplots(figsize=(16,7),facecolor=BG)
    ax.set_facecolor(CARD)
    for sp in ax.spines.values(): sp.set_edgecolor(BORDER)
    x=np.arange(len(clases)); w=0.26
    for bars,vals,col,lbl in [(ax.bar(x-w,pre,w,alpha=0.88,color=CYAN),pre,CYAN,'Precisión'),
                               (ax.bar(x,  rec,w,alpha=0.88,color=ORANGE),rec,ORANGE,'Recall'),
                               (ax.bar(x+w,f1, w,alpha=0.88,color=GREEN),f1,GREEN,'F1-Score')]:
        for b,v in zip(bars,vals):
            ax.text(b.get_x()+b.get_width()/2.,v+0.008,f'{v:.2f}',
                    ha='center',va='bottom',fontsize=8.5,color=TEXT,fontweight='bold')
    ax.axhline(0.90,color=YELLOW,lw=1.2,linestyle='--',alpha=0.6,label='Meta 90%')
    ax.set_title('Precisión · Recall · F1-Score por Gesto',color=TEXT,fontsize=14,fontweight='bold')
    ax.set_xlabel('Gesto',color=MUTED,fontsize=11); ax.set_ylabel('Puntuación',color=MUTED,fontsize=11)
    ax.set_xticks(x); ax.set_xticklabels(labels,rotation=25,ha='right',color=TEXT,fontsize=11)
    ax.set_ylim(0,1.12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_:f'{v:.0%}'))
    ax.legend(facecolor=SURFACE,edgecolor=BORDER,labelcolor=TEXT,fontsize=10); ax.grid(True,axis='y',alpha=0.4)
    ax.text(0.5,1.03,f'Macro Avg — Precisión:{pre.mean():.3f}  Recall:{rec.mean():.3f}  F1:{f1.mean():.3f}',
            transform=ax.transAxes,ha='center',color=MUTED,fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(MODELS_DIR,'reporte_clasificacion.png'),dpi=150,bbox_inches='tight',facecolor=BG)
    plt.close(); print('  ✓ reporte_clasificacion.png')


def grafica_arquitectura(n_clases):
    apply_dark_style()
    fig=plt.figure(figsize=(18,8),facecolor=BG)
    ax=fig.add_subplot(111); ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0,18); ax.set_ylim(-1,10)
    fig.suptitle('Arquitectura de la Red Neuronal — Clasificador de Gestos',
                 color=TEXT,fontsize=15,fontweight='bold',y=0.97)

    layers_info=[
        ('INPUT',     '63 neuronas\n21×3 (x,y,z)',          '#0d2d3a',CYAN,   10),
        ('Dense 128', 'ReLU+BatchNorm\nDropout 0.30',        '#1a3a0d',GREEN,  10),
        ('Dense 64',  'ReLU+BatchNorm\nDropout 0.30',        '#1a3a0d',GREEN,  8),
        ('Dense 32',  'ReLU+BatchNorm\nDropout 0.15',        '#1a3a0d',GREEN,  6),
        ('OUTPUT',    f'{n_clases} neuronas\nSoftmax · {n_clases} gestos','#3a1a0d',ORANGE,n_clases),
    ]
    xs=[1.0,4.2,7.8,11.2,14.8]
    bw=2.6

    for i,((name,desc,bg,fg,dots),x) in enumerate(zip(layers_info,xs)):
        ax.add_patch(FancyBboxPatch((x-bw/2,0.5),bw,8.5,
            boxstyle='round,pad=0.15',facecolor=bg,edgecolor=fg,lw=2.0,alpha=0.9))
        ax.text(x,9.3,name,ha='center',va='center',color=fg,fontsize=12,fontweight='bold')
        dc=min(dots,10)
        for dy in np.linspace(1.5,7.8,dc):
            ax.plot(x,dy,'o',color=fg,markersize=7,alpha=0.85)
        if dots>10: ax.text(x,0.9,'⋮',ha='center',va='center',color=MUTED,fontsize=14)
        ax.text(x,-0.4,desc,ha='center',va='center',color=MUTED,fontsize=8.5,
                multialignment='center',linespacing=1.5)
        if i<len(xs)-1:
            ax.annotate('',xy=(xs[i+1]-bw/2-0.05,4.65),xytext=(x+bw/2+0.05,4.65),
                arrowprops=dict(arrowstyle='->',color=BORDER,lw=2.0))

    total=63*128+128+128*64+64+64*32+32+32*n_clases+n_clases
    ax.text(9,-0.85,
        f'Total parámetros: {total:,}   |   Optimizador: Adam (lr=0.001)   |   Loss: Categorical Crossentropy',
        ha='center',va='center',color=MUTED,fontsize=9.5)
    plt.tight_layout()
    plt.savefig(os.path.join(MODELS_DIR,'arquitectura_red.png'),dpi=150,bbox_inches='tight',facecolor=BG)
    plt.close(); print('  ✓ arquitectura_red.png')


def grafica_dashboard(history, y_true, y_pred, clases):
    apply_dark_style()
    acc     = np.array(history.history['accuracy'])
    val_acc = np.array(history.history['val_accuracy'])
    loss    = np.array(history.history['loss'])
    val_loss= np.array(history.history['val_loss'])
    ep = range(1,len(acc)+1)
    labels=[c.capitalize() for c in clases]
    pre = precision_score(y_true,y_pred,average=None,zero_division=0)
    rec = recall_score(y_true,y_pred,average=None,zero_division=0)
    f1  = f1_score(y_true,y_pred,average=None,zero_division=0)
    cm_n= confusion_matrix(y_true,y_pred).astype(float)
    cm_n= cm_n/cm_n.sum(axis=1)[:,None]

    fig=plt.figure(figsize=(18,10),facecolor=BG)
    fig.suptitle('Dashboard de Evaluación — Modelo de Reconocimiento de Gestos',
                 color=TEXT,fontsize=15,fontweight='bold',y=0.97)
    gs=gridspec.GridSpec(2,3,hspace=0.45,wspace=0.32,left=0.06,right=0.97,top=0.90,bottom=0.07)

    # Accuracy
    a0=fig.add_subplot(gs[0,0]); a0.set_facecolor(CARD)
    for sp in a0.spines.values(): sp.set_edgecolor(BORDER)
    a0.plot(ep,acc*100,color=CYAN,lw=2,label='Train'); a0.plot(ep,val_acc*100,color=ORANGE,lw=2,label='Val',linestyle='--')
    a0.axhline(85,color=GREEN,lw=1,linestyle=':',alpha=0.5)
    a0.set_title('Accuracy (%)',color=TEXT,fontsize=11,fontweight='bold')
    a0.legend(facecolor=SURFACE,edgecolor=BORDER,labelcolor=TEXT,fontsize=9); a0.grid(True); a0.tick_params(colors=MUTED)

    # Loss
    a1=fig.add_subplot(gs[0,1]); a1.set_facecolor(CARD)
    for sp in a1.spines.values(): sp.set_edgecolor(BORDER)
    a1.plot(ep,loss,color=CYAN,lw=2,label='Train'); a1.plot(ep,val_loss,color=RED,lw=2,label='Val',linestyle='--')
    a1.set_title('Loss',color=TEXT,fontsize=11,fontweight='bold')
    a1.legend(facecolor=SURFACE,edgecolor=BORDER,labelcolor=TEXT,fontsize=9); a1.grid(True); a1.tick_params(colors=MUTED)

    # F1 barras
    a2=fig.add_subplot(gs[0,2]); a2.set_facecolor(CARD)
    for sp in a2.spines.values(): sp.set_edgecolor(BORDER)
    cols=[GREEN if v>=0.88 else YELLOW if v>=0.78 else RED for v in f1]
    bars=a2.barh(labels,f1*100,color=cols,alpha=0.88)
    a2.axvline(90,color=YELLOW,lw=1,linestyle='--',alpha=0.6)
    a2.set_xlim(50,108); a2.set_title('F1-Score por Clase (%)',color=TEXT,fontsize=11,fontweight='bold')
    a2.grid(True,axis='x',alpha=0.3); a2.tick_params(colors=TEXT,labelsize=9)
    for b,v in zip(bars,f1): a2.text(b.get_width()+0.5,b.get_y()+b.get_height()/2,f'{v*100:.1f}%',va='center',color=TEXT,fontsize=8.5,fontweight='bold')

    # Matriz confusión
    a3=fig.add_subplot(gs[1,:2]); a3.set_facecolor(CARD)
    sns.heatmap(cm_n,annot=True,fmt='.2f',ax=a3,cmap='Blues',
                xticklabels=[l[:5] for l in labels],yticklabels=[l[:5] for l in labels],
                linewidths=0.4,linecolor=BORDER,vmin=0,vmax=1,
                annot_kws={'size':9},cbar_kws={'shrink':0.7})
    a3.set_title('Matriz de Confusión (Normalizada)',color=TEXT,fontsize=11,fontweight='bold')
    a3.set_xlabel('Predicho',color=MUTED,fontsize=9); a3.set_ylabel('Real',color=MUTED,fontsize=9)
    a3.tick_params(colors=TEXT,labelsize=9)
    a3.set_xticklabels(a3.get_xticklabels(),rotation=30,ha='right',color=TEXT)
    a3.set_yticklabels(a3.get_yticklabels(),rotation=0,color=TEXT)
    plt.setp(a3.collections[0].colorbar.ax.yaxis.get_ticklabels(),color=MUTED)

    # Tabla resumen
    a4=fig.add_subplot(gs[1,2]); a4.set_facecolor(SURFACE); a4.axis('off')
    a4.set_title('Resumen Final',color=TEXT,fontsize=11,fontweight='bold',pad=8)
    rows=[['Métrica','Train','Val'],
          ['Accuracy',f'{acc[-1]*100:.2f}%',f'{val_acc[-1]*100:.2f}%'],
          ['Loss',f'{loss[-1]:.4f}',f'{val_loss[-1]:.4f}'],
          ['Best Val Acc','—',f'{val_acc.max()*100:.2f}%'],
          ['F1 Macro','—',f'{f1.mean()*100:.2f}%'],
          ['Precisión','—',f'{pre.mean()*100:.2f}%'],
          ['Recall','—',f'{rec.mean()*100:.2f}%']]
    for i,row in enumerate(rows):
        y_r=0.96-i*0.135; bg2=CARD if i%2==0 else SURFACE
        a4.add_patch(FancyBboxPatch((0.02,y_r-0.07),0.96,0.10,
            boxstyle='round,pad=0.01',facecolor=bg2,edgecolor=BORDER,lw=0.6,transform=a4.transAxes))
        c0=TEXT if i==0 else MUTED; c1=CYAN if i>0 else TEXT; c2=ORANGE if i>0 else TEXT
        fw='bold'
        a4.text(0.05,y_r-0.02,row[0],transform=a4.transAxes,color=c0,fontsize=9,va='center',fontweight=fw if i==0 else 'normal')
        a4.text(0.55,y_r-0.02,row[1],transform=a4.transAxes,color=c1,fontsize=9,va='center',ha='center',fontweight=fw if i==0 else 'normal')
        a4.text(0.88,y_r-0.02,row[2],transform=a4.transAxes,color=c2,fontsize=9,va='center',ha='center',fontweight=fw if i==0 else 'normal')

    plt.savefig(os.path.join(MODELS_DIR,'dashboard_evaluacion.png'),dpi=150,bbox_inches='tight',facecolor=BG)
    plt.close(); print('  ✓ dashboard_evaluacion.png')


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
def main():
    os.makedirs(MODELS_DIR, exist_ok=True)
    df = cargar_dataset()
    X_tr,X_v,y_tr,y_v,le = preprocesar(df)

    modelo = construir_modelo(len(le.classes_))
    print(f'\n{"═"*54}\n  ENTRENANDO…\n{"═"*54}\n')
    history = entrenar(modelo, X_tr, X_v, y_tr, y_v)
    np.save(LABEL_FILE, le.classes_)

    loss_f, acc_f = modelo.evaluate(X_v, y_v, verbose=0)
    print(f'\n{"═"*54}\n  RESULTADO FINAL\n{"═"*54}')
    print(f'  Val Accuracy : {acc_f*100:.2f}%')
    print(f'  Val Loss     : {loss_f:.4f}')

    # Predicciones para gráficas
    y_pred = np.argmax(modelo.predict(X_v,verbose=0),axis=1)
    y_true = np.argmax(y_v, axis=1)

    print(f'\n{"═"*54}\n  REPORTE POR CLASE\n{"═"*54}')
    print(classification_report(y_true, y_pred, target_names=le.classes_))

    print(f'\n{"═"*54}\n  GENERANDO GRÁFICAS\n{"═"*54}')
    grafica_curvas(history)
    grafica_confusion(y_true, y_pred, le.classes_)
    grafica_reporte(y_true, y_pred, le.classes_)
    grafica_arquitectura(len(le.classes_))
    grafica_dashboard(history, y_true, y_pred, le.classes_)

    print(f'\n  Todas las gráficas en: models/')
    print(f'  Siguiente paso: python reconocer_gestos.py\n')

if __name__=='__main__': main()
