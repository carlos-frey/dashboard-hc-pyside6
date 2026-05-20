import pandas as pd
from datetime import datetime

def processar_inventario_e_os(caminho_inventario, df_os_migrado, caminho_criticidade=None):
    if not caminho_inventario:
        return None
        
    try:
        df_inventario = pd.read_csv(caminho_inventario, sep=';', encoding='utf-8')
    except Exception as e:
        print(f"Erro ao ler arquivo de inventário: {e}")
        return None
        
    if 'Aquisição' in df_inventario.columns:
        df_inventario.rename(columns={'Aquisição': 'Data de Aquisição'}, inplace=True)
        
    df_inventario['Identificador'] = df_inventario['Identificador'].astype(str).str.strip()
    df_inventario['Modelo'] = df_inventario['Modelo'].astype(str).str.strip()
    
    # Adicionar criticidade se a planilha foi fornecida
    if caminho_criticidade:
        try:
            df_crit = pd.read_csv(caminho_criticidade, sep=';', header=5, encoding='utf-8')
            if 'Peso' in df_crit.columns and 'Modelo' in df_crit.columns:
                df_crit_clean = df_crit[['Modelo', 'Peso']].copy()
                df_crit_clean.rename(columns={'Peso': 'Criticidade'}, inplace=True)
                df_crit_clean['Modelo'] = df_crit_clean['Modelo'].astype(str).str.strip()
                df_crit_clean = df_crit_clean.groupby('Modelo').first().reset_index()
                
                df_inventario = pd.merge(df_inventario, df_crit_clean, on='Modelo', how='left')
                df_inventario['Criticidade'] = df_inventario['Criticidade'].fillna(1).astype(float)
        except Exception as e:
            print(f"Erro ao processar planilha de criticidade: {e}")
    
    df_servicos = df_os_migrado.copy()
    
    # Robust Identifier matching
    id_col = 'Identificador'
    if 'Identificador (Patrimônio, ID, TAG)' in df_servicos.columns:
        df_servicos.rename(columns={'Identificador (Patrimônio, ID, TAG)': 'Identificador'}, inplace=True)
    
    if 'Identificador' not in df_servicos.columns:
        # Tenta inferir se houver TAG/Patrimônio
        print("Aviso: Coluna 'Identificador' não encontrada nos serviços migrados.")
        df_servicos['Identificador'] = ''
        
    df_servicos['Identificador'] = df_servicos['Identificador'].astype(str).str.strip()
    
    # Cleaning cost
    if 'Custo' in df_servicos.columns:
        df_servicos['Custo_Limpo'] = df_servicos['Custo'].astype(str).str.replace(r'[^\d,\.]', '', regex=True).str.replace(',', '.')
        df_servicos['Custo_Limpo'] = pd.to_numeric(df_servicos['Custo_Limpo'], errors='coerce').fillna(0)
    else:
        df_servicos['Custo_Limpo'] = 0
        
    # Group costs
    df_custo_agregado = df_servicos.groupby('Identificador')['Custo_Limpo'].sum().reset_index()
    df_custo_agregado.rename(columns={'Custo_Limpo': 'Custo total externo'}, inplace=True)
    
    # Merge Costs
    df_final = pd.merge(df_inventario, df_custo_agregado, on='Identificador', how='left')
    df_final['Custo total externo'] = df_final['Custo total externo'].fillna(0)
    df_final['Status'] = 'Em uso' # Default
    
    # Assign Criticidade if not loaded by the external file
    if 'Criticidade' not in df_final.columns:
        if 'Equipamento Crítico' in df_final.columns:
            # Convert SIM to 3, NÃO to 1 as mock does
            df_final['Criticidade'] = df_final['Equipamento Crítico'].apply(lambda x: 3 if str(x).upper() == 'SIM' else 1)
        else:
            df_final['Criticidade'] = 1
        
    # Cleaning dates
    df_final['Data de Aquisição'] = pd.to_datetime(df_final['Data de Aquisição'], errors='coerce')
    
    # Generate Prioridade score
    # Score 0 to 100 based on Criticidade, Custo, Idade
    # Age > 10 years gets 20 pts
    data_limite = datetime.now() - pd.DateOffset(years=10)
    idade_pts = ((df_final['Data de Aquisição'] < data_limite) * 20).fillna(0)
    
    # Criticidade gets up to 50 pts (1=16.6, 2=33.3, 3=50)
    crit_pts = (df_final['Criticidade'] / 3.0) * 50
    
    # Cost gets up to 30 pts 
    max_custo = df_final['Custo total externo'].max()
    if max_custo > 0:
        custo_pts = (df_final['Custo total externo'] / max_custo) * 30
    else:
        custo_pts = 0
        
    df_final['Score'] = idade_pts + crit_pts + custo_pts
    
    # Convert Data to string for UI
    df_final['Data de Aquisição'] = df_final['Data de Aquisição'].dt.strftime('%Y-%m-%d').fillna('2015-01-01')
    
    # Clean valor
    if 'Valor (R$)' in df_final.columns:
        val_str = df_final['Valor (R$)'].astype(str).str.replace(r'[^\d,\.]', '', regex=True).str.replace(',', '.')
        df_final['Valor'] = pd.to_numeric(val_str, errors='coerce').fillna(0)
    else:
        df_final['Valor'] = 0
        
    df_final.sort_values(by='Score', ascending=False, inplace=True)
    return df_final


def integrar_dados_dashboard(caminho_inventario, df_os_migrado, caminho_criticidade=None):
    df_equip = processar_inventario_e_os(caminho_inventario, df_os_migrado, caminho_criticidade)
    if df_equip is None:
        return None
        
    resultado = []
    
    # Prepara df_os para agrupamento
    df_os = df_os_migrado.copy()
    if 'Identificador (Patrimônio, ID, TAG)' in df_os.columns:
        df_os.rename(columns={'Identificador (Patrimônio, ID, TAG)': 'Identificador'}, inplace=True)
    
    if 'Identificador' not in df_os.columns:
        df_os['Identificador'] = ''
        
    df_os['Identificador'] = df_os['Identificador'].astype(str).str.strip()
    
    if 'Custo' in df_os.columns:
        df_os['Custo_Limpo'] = df_os['Custo'].astype(str).str.replace(r'[^\d,\.]', '', regex=True).str.replace(',', '.')
        df_os['Custo_Limpo'] = pd.to_numeric(df_os['Custo_Limpo'], errors='coerce').fillna(0)
    else:
        df_os['Custo_Limpo'] = 0
        
    # Usando Abertura que é o nome padronizado agora
    if 'Abertura' in df_os.columns:
        df_os['Data_Limpa'] = pd.to_datetime(df_os['Abertura'], errors='coerce', dayfirst=True)
    else:
        df_os['Data_Limpa'] = pd.NaT
        
    df_os['Data_Str'] = df_os['Data_Limpa'].dt.strftime('%Y-%m-%d').fillna('2020-01-01')
    
    if 'Serviço;Assistência' in df_os.columns:
        df_os['Desc'] = df_os['Serviço;Assistência'].fillna('Manutenção')
    else:
        df_os['Desc'] = 'Manutenção'
    
    os_por_equipamento = df_os.groupby('Identificador')
    
    for _, row in df_equip.iterrows():
        ident = str(row['Identificador'])
        
        eq_dict = {
            "modelo": str(row.get('Modelo', 'Desconhecido')),
            "setor": str(row.get('Localização', 'Desconhecido')),
            "criticidade": int(row.get('Criticidade', 1)),
            "data_aquisicao": str(row.get('Data de Aquisição', '2015-01-01')),
            "status": str(row.get('Status', 'Em uso')),
            "valor": float(row.get('Valor', 0)),
            "score": float(row.get('Score', 50)),
            "identificador": ident,
            "os": []
        }
        
        if ident in os_por_equipamento.groups:
            os_data = os_por_equipamento.get_group(ident)
            for _, os_row in os_data.iterrows():
                eq_dict["os"].append({
                    "data": os_row['Data_Str'],
                    "custo": float(os_row['Custo_Limpo']),
                    "desc": os_row['Desc']
                })
                
        resultado.append(eq_dict)
        
    return resultado
