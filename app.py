if submitted:
            # Validação para 'Data de Início' em ambas as abas
            if "Data de Início" in new_data and new_data["Data de Início"]:
                try:
                    data_inicio_obj = datetime.strptime(new_data["Data de Início"], "%d/%m/%Y").date()
                except ValueError:
                    st.error("❌ Formato de data inválido. Use DD/MM/YYYY.")
                    return

            df = st.session_state[df_name].copy()
            idx = df[df["ID"] == record["ID"]].index
            if not idx.empty:
                # Lógica para logar alterações
                for c in cols:
                    if c in df.columns:
                        antigo = df.loc[idx[0], c]
                        novo = new_data.get(c, "")
                        if str(antigo) != str(novo):
                            registrar_log(
                                aba=ABA_MAP[df_name],
                                acao="Editar",
                                item_id=record["ID"],
                                campo=c,
                                valor_anterior=antigo,
                                valor_novo=novo,
                                detalhe=f"Registro {record['ID']} alterado em {c}."
                            )
                            df.loc[idx, c] = novo

            st.session_state[df_name] = df
            save_csv(df, csv_path)

            # --- Lógica de atualização de Vagas com base em Candidatos ---
            if df_name == "candidatos_df":
                vaga_id = record.get("VagaID")
                vagas_df = st.session_state.vagas_df.copy()
                idx_vaga = vagas_df[vagas_df["ID"] == vaga_id].index
                
                if not idx_vaga.empty:
                    antigo_status_vaga = vagas_df.loc[idx_vaga[0], "Status"]
                    novo_status_candidato = new_data.get("Status")
                    nova_data_inicio_str = new_data.get("Data de Início")
                    
                    # Regra 1: Candidato Validado sem Data de Início -> Vaga Ag. Inicio
                    if novo_status_candidato == "Validado" and not nova_data_inicio_str:
                        if antigo_status_vaga != "Ag. Inicio":
                            vagas_df.loc[idx_vaga, "Status"] = "Ag. Inicio"
                            st.info("🔄 Status da vaga alterado para 'Ag. Inicio' (candidato validado).")
                            registrar_log(
                                aba="Vagas",
                                acao="Atualização Automática",
                                item_id=vaga_id,
                                campo="Status",
                                valor_anterior=antigo_status_vaga,
                                valor_novo="Ag. Inicio",
                                detalhe=f"Vaga alterada automaticamente ao validar candidato {record['ID']}."
                            )
                    # Regra 2: Candidato Validado com Data de Início igual ou anterior à data atual -> Vaga Fechada
                    elif novo_status_candidato == "Validado" and nova_data_inicio_str:
                        try:
                            data_inicio_obj = datetime.strptime(nova_data_inicio_str, "%d/%m/%Y").date()
                            if data_inicio_obj <= date.today():
                                if antigo_status_vaga != "Fechada":
                                    vagas_df.loc[idx_vaga, "Status"] = "Fechada"
                                    st.success("✅ Status da vaga alterado para 'Fechada' (candidato contratado).")
                                    registrar_log(
                                        aba="Vagas",
                                        acao="Atualização Automática",
                                        item_id=vaga_id,
                                        campo="Status",
                                        valor_anterior=antigo_status_vaga,
                                        valor_novo="Fechada",
                                        detalhe=f"Vaga fechada automaticamente ao validar e preencher a data de início do candidato {record['ID']}."
                                    )
                        except ValueError:
                            # A validação já é feita no início da função, mas é bom ter uma redundância
                            pass

                    # Regra 3: Se o status do candidato mudar para algo diferente de "Validado" e a vaga estava fechada ou ag. inicio, reabrir a vaga
                    elif antigo_status_vaga in ["Ag. Inicio", "Fechada"] and novo_status_candidato != "Validado":
                        vagas_df.loc[idx_vaga, "Status"] = "Aberta"
                        st.info("🔄 Vaga reaberta automaticamente!")
                        registrar_log(
                            aba="Vagas",
                            acao="Atualização Automática",
                            item_id=vaga_id,
                            campo="Status",
                            valor_anterior=antigo_status_vaga,
                            valor_novo="Aberta",
                            detalhe=f"Vaga reaberta automaticamente ao reverter validação do candidato {record['ID']}."
                        )
                    
                st.session_state.vagas_df = vagas_df
                save_csv(vagas_df, VAGAS_CSV)

            st.success("✅ Registro atualizado com sucesso!")
            st.session_state.edit_mode = None
            st.session_state.edit_record = {}
            st.rerun()
