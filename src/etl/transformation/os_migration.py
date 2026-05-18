import pandas as pd

def migrar_dados_servico(caminho_os_antiga=None, caminho_os_atual=None):
    """
    Migra e unifica os dados das ordens de serviço antigas e recentes
    para um novo formato em um único DataFrame.
    
    Aceita pelo menos uma das planilhas. Ignora e sinaliza caso uma esteja faltando.
    """
    if not caminho_os_antiga and not caminho_os_atual:
        raise ValueError("Pelo menos um arquivo de Ordens de Serviço (antigo ou atual) deve ser fornecido.")

    df_recente = pd.DataFrame()
    df_contrato_sl = pd.DataFrame()
    
    # 1. Carregar planilha atual (se fornecida)
    if caminho_os_atual:
        try:
            df_recente = pd.read_csv(caminho_os_atual, sep=';', engine='python')
            print(f"Planilha atual carregada: {caminho_os_atual}")
        except FileNotFoundError:
            print(f"Aviso: Planilha de OS atual não encontrada em '{caminho_os_atual}'.")

    # 2. Carregar planilha antiga (se fornecida)
    if caminho_os_antiga:
        try:
            # O formato antigo usa skiprows=[0]
            df_contrato_sl = pd.read_csv(caminho_os_antiga, sep=';', skiprows=[0], engine='python')
            print(f"Planilha antiga carregada: {caminho_os_antiga}")
        except FileNotFoundError:
            print(f"Aviso: Planilha de OS antiga não encontrada em '{caminho_os_antiga}'.")

    # Se ambas falharem na leitura por arquivo inexistente apesar de o path ser fornecido
    if df_recente.empty and df_contrato_sl.empty:
        raise ValueError("Nenhum dado pôde ser extraído das planilhas fornecidas.")

    # 3. Estabelecer o esquema base
    colunas_esperadas = [
        'OS', 'Equipamento', 'Modelo', 'Fabricante', 'Abertura', 'Fechamento', 
        'Serviço;Assistência', 'Custo', 'Identificador (Patrimônio, ID, TAG)'
    ]
    
    if not df_recente.empty:
        df_migrado = df_recente.copy()
        if 'Identificador (Patrimônio, ID, TAG)' not in df_migrado.columns:
            df_migrado['Identificador (Patrimônio, ID, TAG)'] = ''
    else:
        # Cria um DataFrame vazio com a estrutura das colunas modernas caso só tenha a velha
        df_migrado = pd.DataFrame(columns=colunas_esperadas)

    # 4. Mapeamento do formato legado para o novo formato
    mapeamento = {
        'O.S': 'OS', 'Tipo': 'Equipamento', 'Modelo': 'Modelo', 'Marca': 'Fabricante',
        'Data Início SE': 'Abertura', 'Data Conclusão SE': 'Fechamento',
        'Fornecedor': 'Serviço;Assistência', 'Custo': 'Custo'
    }

    # 5. Iterar e injetar linhas antigas, se existirem
    novas_linhas = []
    if not df_contrato_sl.empty:
        for _, row in df_contrato_sl.iterrows():
            nova_linha = {col: None for col in df_migrado.columns}
            
            # Aplica o de-para iterativo
            for col_recente, col_sl in mapeamento.items():
                if col_sl in row:
                    nova_linha[col_recente] = row[col_sl]
            
            # Gera o Identificador único a partir da TAG + Patrimônio
            tag = str(row['TAG']) if 'TAG' in row and pd.notna(row['TAG']) else ''
            patrimonio = str(row['Patrimônio']) if 'Patrimônio' in row and pd.notna(row['Patrimônio']) else ''
            identificador = f"{tag},{patrimonio}" if tag and patrimonio else tag or patrimonio
            
            nova_linha['Identificador (Patrimônio, ID, TAG)'] = identificador
            novas_linhas.append(nova_linha)

    # 6. Concatena os DataFrames
    if novas_linhas:
        df_migrado = pd.concat([df_migrado, pd.DataFrame(novas_linhas)], ignore_index=True)
    
    print("Processamento de Ordens de Serviço finalizado.")
    return df_migrado