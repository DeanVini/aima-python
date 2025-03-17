from csp import NaryCSP, Constraint

# -------------------------------
# Dados do Problema
# -------------------------------

# Matriz de Pedidos: Cada linha representa um pedido; cada coluna, um item.
# Exemplo: 5 pedidos e 5 itens.

orders = [ # Mesmo exemplo do Problema da Seleção de Pedidos Ótima
    [3, 0, 1, 0, 0], # Pedido 1: total = 4
    [0, 1, 0, 1, 0], # Pedido 2: total = 2
    [0, 0, 1, 0, 2], # Pedido 3: total = 3
    [1, 0, 2, 1, 1], # Pedido 4: total = 5
    [0, 1, 0, 0, 0]  # Pedido 5: total = 1
]

# Total de unidades por pedido (soma das linhas)
order_totals = [sum(o) for o in orders]  # [4, 2, 3, 5, 1]

# Matriz de Corredores: Cada linha representa um corredor; cada coluna, a disponibilidade do item.
corridors = [
    [2, 1, 1, 0, 1], # Corredor 1
    [2, 1, 2, 0, 1], # Corredor 2
    [0, 2, 0, 1, 2], # Corredor 3
    [2, 1, 0, 1, 1], # Corredor 4
    [0, 1, 2, 1, 2]  # Corredor 5
]

# Limites para o total de unidades coletadas
LB = 5  # Limite inferior
UB = 12 # Limite superior

# -------------------------------
# Definição do CSP
# -------------------------------

# 1. Conjunto de Variáveis (X)
# Para os pedidos: variáveis "Pedido1", "Pedido2", ..., "Pedido5"
# Para os corredores: variáveis "Corredor1", "Corredor2", ..., "Corredor5"
domains = {}
for o in range(len(orders)):
    domains[f"Pedido{o + 1}"] = {0, 1} # 1: pedido selecionado; 0: não selecionado
for a in range(len(corridors)):
    domains[f"Corredor{a + 1}"] = {0, 1} # 1: corredor utilizado; 0: não utilizado
print(domains)

# 2. Conjunto de Restrições (C)
constraints = []

# 1. Restrição do total de unidades coletadas (somente dos pedidos)
# A soma total das unidades dos pedidos selecionados deve estar entre LB e UB.
def total_demand_constraint(*order_vals):
    total = sum(total * val for total, val in zip(order_totals, order_vals))
    return LB <= total <= UB

orders_variables = tuple(f"Pedido{i+1}" for i in range(len(orders)))
constraints.append(Constraint(orders_variables, total_demand_constraint))

# 2. Restrição para cada item: a demanda (dos pedidos selecionados) deve ser atendida
# Para cada item (coluna), a demanda dos pedidos selecionados deve ser atendida pela capacidade dos corredores utilizados.
def item_constraint_factory(i):
    def constraint_func(*vals):
        # Os primeiros 5 valores são referentes às variáveis dos pedidos;
        order_vals = vals[:5]
        # Os próximos 5 valores são referentes às variáveis dos corredores.
        corridor_vals = vals[5:]
        demand = sum(orders[o][i] * order_vals[o] for o in range(5))
        capacity = sum(corridors[a][i] * corridor_vals[a] for a in range(5))
        return demand <= capacity
    return constraint_func

# Para cada item (0 a 4), o escopo é: todos os pedidos e todos os corredores
itens_num  = len(orders[0])
all_variables = orders_variables + tuple(f"Corredor{j+1}" for j in range(len(corridors)))
for j in range(len(orders)):
    print(all_variables)
    constraints.append(Constraint(all_variables, item_constraint_factory(j)))

# Criando a instância do CSP utilizando a classe NaryCSP
csp_instance = NaryCSP(domains, constraints)

# -------------------------------
# Busca por Soluções (Backtracking)
# -------------------------------
def backtracking(csp, assignment={}):
    if len(assignment) == len(csp.domains):
        yield assignment
    else:
        # Seleciona uma variável não atribuída (pode usar MRV, já que todos possuem domínio de tamanho 2)
        unassigned = [v for v in csp.domains if v not in assignment]
        var = min(unassigned, key=lambda v: len(csp.domains[v]))
        for value in sorted(csp.domains[var]):
            new_assignment = assignment.copy()
            new_assignment[var] = value
            if csp.consistent(new_assignment):
                yield from backtracking(csp, new_assignment)

# -------------------------------
# Cálculo da Função Objetivo
# -------------------------------
# Produtividade = (total de unidades dos pedidos selecionados) / (número de corredores utilizados)
def objective(solution):
    total_units = sum(order_totals[o] * solution[f"Pedido{o + 1}"] for o in range(len(orders)))
    num_corridors = sum(solution[f"Corredor{a + 1}"] for a in range(len(corridors)))
    return total_units / num_corridors if num_corridors > 0 else -1

# Coleta todas as soluções viáveis
solutions = list(backtracking(csp_instance))

# -------------------------------
# Impressão dos Resultados
# -------------------------------
def print_solution(sol, index):
    orders_selected = [f"Pedido{o + 1}" for o in range(len(orders)) if sol[f"Pedido{o + 1}"] == 1]
    corridors_selected = [f"Corredor{a + 1}" for a in range(len(corridors)) if sol[f"Corredor{a + 1}"] == 1]
    total_units = sum(order_totals[o] * sol[f"Pedido{o + 1}"] for o in range(len(orders)))
    num_corridors = sum(sol[f"Corredor{a + 1}"] for a in range(len(corridors)))
    obj = objective(sol)
    print(f"Wave {index}:")
    print(f"  Pedidos selecionados   : {', '.join(orders_selected) if orders_selected else 'Nenhum'}")
    print(f"  Corredores selecionados: {', '.join(corridors_selected) if corridors_selected else 'Nenhum'}")
    print(f"  Total de unidades      : {total_units}")
    print(f"  Número de corredores   : {num_corridors}")
    print(f"  Valor objetivo         : {obj:.2f}")
    print("-" * 50)

# Imprime todas as waves viáveis encontradas
print("\nWaves viáveis encontradas:")
for idx, sol in enumerate(solutions, start=1):
    print_solution(sol, idx)

# Seleciona a melhor solução (aquela com o maior valor objetivo)
best_solution = None
best_obj = -1
best_index = -1
for idx, sol in enumerate(solutions, start=1):
    obj_val = objective(sol)
    if obj_val >= best_obj:
        best_obj = obj_val
        best_solution = sol
        best_index = idx

print("\nMelhor Wave encontrada:")
print_solution(best_solution, best_index)
