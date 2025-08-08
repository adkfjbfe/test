import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import matplotlib.font_manager as fm

# CSV 파일 로드
df = pd.read_csv("출자구조.CSV", encoding="cp949")

# 한글 폰트 설정
font_path = 'C:\\Windows\\Fonts\\malgun.ttf'
font_name = fm.FontProperties(fname=font_path).get_name()
plt.rc('font', family=font_name)
plt.rcParams['axes.unicode_minus'] = False

# 사용자 입력 기관
UserInput = ['국토교통부']

# 소유 관계 탐색 함수
def org_owners(df, target_orgs):
    results = {}
    for org in target_orgs:
        owners = df[df['피소유 기관'] == org]['소유 기관'].tolist()
        if owners:
            results[org] = owners
            sub_results = org_owners(df, owners)
            for key, value in sub_results.items():
                results[key] = value
    return results

def org_owning(df, target_orgs):
    results = {}
    for org in target_orgs:
        owned = df[df['소유 기관'] == org]['피소유 기관'].tolist()
        if owned:
            results[org] = owned
            sub_results = org_owning(df, owned)
            for key, value in sub_results.items():
                results[key] = value
    return results
# 관계 추출
orgOwners = org_owners(df, UserInput)
orgOwning = org_owning(df, UserInput)

# 그래프 생성
DI = nx.DiGraph()

# 노드 수집
all_nodes = set(orgOwners.keys()) | set(orgOwning.keys())
for owners in orgOwners.values():
    all_nodes.update(owners)
for owned in orgOwning.values():
    all_nodes.update(owned)
DI.add_nodes_from(all_nodes)
DI.add_nodes_from(UserInput)

# 엣지 추가
edges_userOwner = []
edges_userOwns = []
orgs_notuser = []

for owner, owned_list in orgOwning.items():
    for owned in owned_list:
        weight = df[(df['피소유 기관'] == owned) & (df['소유 기관'] == owner)]['지분'].tolist()
        if weight:
            DI.add_edge(owner, owned, weight=weight[0])
            if owner in UserInput:
                edges_userOwner.append((owner, owned))
            else:
                orgs_notuser.append((owner, owned))

for owned, owner_list in orgOwners.items():
    for owner in owner_list:
        weight = df[(df['피소유 기관'] == owned) & (df['소유 기관'] == owner)]['지분'].tolist()
        if weight:
            DI.add_edge(owner, owned, weight=weight[0])
            if owned in UserInput:
                edges_userOwns.append((owner, owned))
            else:
                orgs_notuser.append((owner, owned))

# 위계값 설정
hierarchy = {}
for _, row in df.iterrows():
    hierarchy[row['피소유 기관']] = row['위계(피소유기관)']
    hierarchy[row['소유 기관']] = row['위계(소유기관)']

# 노드 위치 계산
level_nodes = {}
for node in DI.nodes():
    level = hierarchy.get(node, max(hierarchy.values()) + 1)
    if level not in level_nodes:
        level_nodes[level] = []
    level_nodes[level].append(node)

pos = {}
y_gap = 100
x_gap = 300

for level in sorted(level_nodes.keys()):
    nodes = level_nodes[level]
    x = -level * x_gap
    y_start = -((len(nodes) - 1) * y_gap) / 2
    for i, node in enumerate(nodes):
        pos[node] = (x, y_start + i * y_gap)


# 중심 노드 위치 조정
for node in UserInput:
    if node in pos:
        avg_x = np.mean([x for x, y in pos.values()])
        pos[node] = (avg_x, pos[node][1])

# 그래프 시각화
plt.figure(figsize=(12, 10))
nx.draw_networkx_nodes(DI, pos, node_color='skyblue', node_size=300)

connect_style = 'arc3,rad=0.1'
nx.draw_networkx_edges(DI, pos, edgelist=edges_userOwns, connectionstyle=connect_style, edge_color='green', arrowstyle='->', arrowsize=15, width=2)
nx.draw_networkx_edges(DI, pos, edgelist=edges_userOwner, connectionstyle=connect_style, edge_color='red', arrowstyle='->', arrowsize=15, width=2)
nx.draw_networkx_edges(DI, pos, edgelist=orgs_notuser, connectionstyle=connect_style, edge_color='blue', arrowstyle='->', arrowsize=15, width=2)

nx.draw_networkx_labels(DI, pos, font_size=10, font_family='malgun gothic')
labels = nx.get_edge_attributes(DI, 'weight')
nx.draw_networkx_edge_labels(DI, pos, edge_labels=labels, label_pos=0.4, font_family='malgun gothic', font_size=9)

plt.title("공기업 출자구조", fontsize=15)
plt.axis('off')
plt.tight_layout()
plt.show()
