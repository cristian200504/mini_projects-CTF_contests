from collections import deque

def solve_maze(target: int) -> str:
    for s_val in [1, 10, 13, 18, 19, 26, 37, 42, 66, 91, 98, 133, 149, 199, 598]:
        queue = deque([(s_val, "")])
        visited = {s_val}
        while queue:
            curr, path = queue.popleft()
            if curr == target: return path
            if len(path) >= 8: continue
            
            nxt_a = curr * 2
            if nxt_a not in visited and nxt_a < 3000:
                visited.add(nxt_a)
                queue.append((nxt_a, path + "A"))
            
            if (curr - 1) % 3 == 0:
                nxt_b = (curr - 1) // 3
                if nxt_b not in visited and nxt_b > 0:
                    visited.add(nxt_b)
                    queue.append((nxt_b, path + "B"))
    return "NOT_FOUND"

print(f"Target 160: {solve_maze(160)}")
print(f"Target 104: {solve_maze(104)}")
print(f"Target 172: {solve_maze(172)}")
print(f"Target 265: {solve_maze(265)}")
print(f"Target 98: {solve_maze(98)}")
print(f"Target 97: {solve_maze(97)}")
