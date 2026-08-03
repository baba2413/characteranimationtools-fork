import copy
import os

class BVHNode:
    def __init__(self, name, type_):
        self.name = name
        self.type = type_  # 'ROOT', 'JOINT', 'End Site'
        self.offset = [0.0, 0.0, 0.0]
        self.channels = []
        self.children = []
        self.parent = None

def parse_bvh_hierarchy(hierarchy_lines):
    root = None
    current = None
    end_site_counter = 0
    
    for line in hierarchy_lines:
        line_str = line.strip()
        if not line_str or line_str.startswith('HIERARCHY'):
            continue
        tokens = line_str.split()
        
        if tokens[0] in ['ROOT', 'JOINT']:
            node = BVHNode(tokens[1], tokens[0])
            if current is not None:
                current.children.append(node)
                node.parent = current
            else:
                root = node
            current = node
        elif tokens[0] == 'End' and tokens[1] == 'Site':
            end_site_counter += 1
            node = BVHNode(f"EndSite_{current.name}_{end_site_counter}", 'End Site')
            current.children.append(node)
            node.parent = current
            current = node
        elif tokens[0] == '{':
            pass
        elif tokens[0] == '}':
            if current is not None:
                current = current.parent
        elif tokens[0] == 'OFFSET':
            if current is not None:
                current.offset = [float(tokens[1]), float(tokens[2]), float(tokens[3])]
        elif tokens[0] == 'CHANNELS':
            if current is not None:
                current.channels = tokens[2:]
                
    return root

def prune_joints(node, target_substrings):
    new_children = []
    for child in node.children:
        # 대소문자 구분 없이 타겟 키워드 매칭 확인
        should_remove = any(sub.lower() in child.name.lower() for sub in target_substrings) and child.type in ['ROOT', 'JOINT']
        if should_remove:
            # [원리 고정] 자식 관절을 트리에서 제거하되, 자식이 가지던 원본 오프셋을 부모의 End Site로 이관합니다.
            # 이 처리가 수행되어야 팔꿈치-어깨 골격 링크의 방향 벡터가 유지되어 만세 현상이 발생하지 않습니다.
            end_site = BVHNode(f"EndSite_{node.name}_Pruned", 'End Site')
            end_site.offset = child.offset[:]
            end_site.parent = node
            new_children.append(end_site)
        else:
            prune_joints(child, target_substrings)
            new_children.append(child)
    node.children = new_children

def get_channel_nodes(node):
    nodes = []
    if node.type in ['ROOT', 'JOINT'] and node.channels:
        nodes.append(node)
    for child in node.children:
        nodes.extend(get_channel_nodes(child))
    return nodes

def serialize_hierarchy(node, indent=""):
    lines = []
    if node.type == 'ROOT':
        lines.append(f"{indent}ROOT {node.name}\n")
    elif node.type == 'JOINT':
        lines.append(f"{indent}JOINT {node.name}\n")
    elif node.type == 'End Site':
        lines.append(f"{indent}End Site\n")
        
    lines.append(f"{indent}{{\n")
    lines.append(f"{indent}  OFFSET {node.offset[0]:.6f} {node.offset[1]:.6f} {node.offset[2]:.6f}\n")
    if node.type in ['ROOT', 'JOINT'] and node.channels:
        ch_str = " ".join(node.channels)
        lines.append(f"{indent}  CHANNELS {len(node.channels)} {ch_str}\n")
        
    for child in node.children:
        lines.extend(serialize_hierarchy(child, indent + "  "))
        
    lines.append(f"{indent}}}\n")
    return lines

def strip_hands_perfect(input_path, output_path, target_substrings=['hand', 'finger']):
    if not os.path.exists(input_path):
        print(f"Error: 원본 파일 경로를 확인하세요 -> {input_path}")
        return

    with open(input_path, 'r') as f:
        lines = f.readlines()
        
    hierarchy_lines = []
    motion_lines = []
    is_motion = False
    
    for line in lines:
        if line.strip().startswith('MOTION'):
            is_motion = True
        if is_motion:
            motion_lines.append(line)
        else:
            hierarchy_lines.append(line)
            
    # 1. 원본 스켈레톤 구조 해석
    original_root = parse_bvh_hierarchy(hierarchy_lines)
    if not original_root:
        print("Error: BVH 구조 분석 실패.")
        return
    
    # 2. 오리지널 모션 데이터 컬럼 인덱스 매핑 테이블 생성
    original_nodes = get_channel_nodes(original_root)
    col_idx = 0
    node_to_indices = {}
    for n in original_nodes:
        num_ch = len(n.channels)
        node_to_indices[n.name] = list(range(col_idx, col_idx + num_ch))
        col_idx += num_ch
        
    # 3. 트리 깊은 복사 후 손목 이하 노드 일괄 Pruning 및 오프셋 보정 수식 주입
    pruned_root = copy.deepcopy(original_root)
    prune_joints(pruned_root, target_substrings)
    
    # 4. 필터링 후 생존한 관절 데이터 컬럼만 정확히 골라내기
    retained_nodes = get_channel_nodes(pruned_root)
    retained_names = set(n.name for n in retained_nodes)
    
    cols_to_keep = []
    for n in original_nodes:
        if n.name in retained_names:
            cols_to_keep.extend(node_to_indices[n.name])
            
    # 5. 정제된 뼈대 데이터 문자열화
    new_hierarchy_strings = serialize_hierarchy(pruned_root)
    
    # 6. MOTION 행렬 컬럼 슬라이싱 (한 칸의 오차도 없이 데이터 추출)
    new_motion_strings = []
    for line in motion_lines:
        line_strip = line.strip()
        if not line_strip:
            continue
        tokens = line_strip.split()
        if tokens[0] == 'MOTION':
            new_motion_strings.append(line)
        elif tokens[0] == 'Frames:':
            new_motion_strings.append(line)
        elif tokens[0] == 'Frame' and tokens[1] == 'Time:':
            new_motion_strings.append(line)
        else:
            # 각 프레임별 순수 수치 추출
            new_tokens = [tokens[c] for c in cols_to_keep]
            new_motion_strings.append(" ".join(new_tokens) + "\n")
            
    # 7. 물리 축 변환 및 오염이 완전히 배제된 새 고정 규격 파일 쓰기
    with open(output_path, 'w') as f:
        f.write("HIERARCHY\n")
        f.writelines(new_hierarchy_strings)
        f.writelines(new_motion_strings)
        
    print(f"🎯 강화학습 최적화 변환 완료: {input_path} -> {output_path}")
    print(f"   (기존 관절 수: {len(original_nodes)}개 -> 정제 후 관절 수: {len(retained_nodes)}개)")

# --- 실행부 ---
if __name__ == "__main__":
    # CharacterAnimationTools에서 load_hand=False 상태 등으로 추출한 오리지널 bvh 경로를 기입하세요.
    input_bvh_file = "data/squat_bvh_no_hand.bvh"
    output_bvh_file = "nohand.bvh"
    
    # 지우고자 하는 관절 명칭 키워드 리스트 (대소문자 무관 매칭)
    # CharacterAnimationTools 표준 트리에서 손목(wrist) 및 손(hand)을 통째로 커트합니다.
    strip_hands_perfect(input_bvh_file, output_bvh_file, target_substrings=['wrist','hand', 'finger'])