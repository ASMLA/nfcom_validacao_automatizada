class CT004_CST:

    def validar(self, item, resultado_item, classificacao):
        imp = item.get("IMPOSTO_REFORMA", {})
        cst_json = str(imp.get("COD_CST", "")).strip()
        cst_esp = classificacao.get("cst_esperado")

        if cst_json != cst_esp:
            resultado_item["CT004"] = {
                "erro": True,
                "esperado": cst_esp,
                "encontrado": cst_json
            }
        else:
            resultado_item["CT004"] = {
                "erro": False,
                "esperado": cst_esp,
                "encontrado": cst_json
            }
