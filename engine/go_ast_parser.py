# Docker 源码学习系统 — Go 源码 AST 解析引擎

"""
真实的 Go 源码解析引擎，从 Docker (moby/moby) 仓库获取源码，
解析关键结构体、接口、函数及其关系。

核心功能：
1. 从 GitHub 获取 Docker 源码文件
2. 解析 Go AST（结构体、接口、函数、方法）
3. 提取代码关系（调用、实现、组合）
4. 与知识图谱关联，增强研究报告
"""

import re
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional
from datetime import datetime


# ============================================================
# Docker 源码文件配置
# ============================================================

DOCKER_SOURCE_FILES = {
    "container": {
        "description": "容器核心实现",
        "files": [
            {
                "path": "container/container.go",
                "url": "https://raw.githubusercontent.com/moby/moby/master/container/container.go",
                "key_structs": ["Container", "State", "Config"],
                "key_funcs": ["NewContainer", "containerCreate"],
            },
            {
                "path": "container/container_unit_test.go",
                "url": "https://raw.githubusercontent.com/moby/moby/master/container/container_unit_test.go",
                "key_structs": [],
                "key_funcs": [],
            },
        ],
    },
    "daemon": {
        "description": "守护进程核心逻辑",
        "files": [
            {
                "path": "daemon/daemon.go",
                "url": "https://raw.githubusercontent.com/moby/moby/master/daemon/daemon.go",
                "key_structs": ["Daemon"],
                "key_funcs": ["start", "containerCreate", "ContainerCreate"],
            },
        ],
    },
    "client": {
        "description": "Docker API 客户端",
        "files": [
            {
                "path": "client/client.go",
                "url": "https://raw.githubusercontent.com/moby/moby/master/client/client.go",
                "key_structs": ["Client"],
                "key_funcs": ["NewClient", "NewClientWithOpts"],
            },
            {
                "path": "client/container_create.go",
                "url": "https://raw.githubusercontent.com/moby/moby/master/client/container_create.go",
                "key_structs": [],
                "key_funcs": ["ContainerCreate"],
            },
        ],
    },
    "api_types": {
        "description": "API 类型定义",
        "files": [
            {
                "path": "api/types/client.go",
                "url": "https://raw.githubusercontent.com/moby/moby/master/api/types/client.go",
                "key_structs": ["Client", "DockerClient"],
                "key_funcs": [],
            },
            {
                "path": "api/types/container/container.go",
                "url": "https://raw.githubusercontent.com/moby/moby/master/api/types/container/container.go",
                "key_structs": ["Config", "HostConfig", "NetworkingConfig"],
                "key_funcs": [],
            },
        ],
    },
    "runtime": {
        "description": "容器运行时",
        "files": [
            {
                "path": "daemon/runtime.go",
                "url": "https://raw.githubusercontent.com/moby/moby/master/daemon/runtime.go",
                "key_structs": ["Runtime"],
                "key_funcs": [],
            },
        ],
    },
    "image": {
        "description": "镜像管理",
        "files": [
            {
                "path": "image/image.go",
                "url": "https://raw.githubusercontent.com/moby/moby/master/image/image.go",
                "key_structs": ["Image", "Store"],
                "key_funcs": [],
            },
            {
                "path": "image/store.go",
                "url": "https://raw.githubusercontent.com/moby/moby/master/image/store.go",
                "key_structs": ["Store"],
                "key_funcs": [],
            },
        ],
    },
    "layer": {
        "description": "镜像层",
        "files": [
            {
                "path": "layer/layer.go",
                "url": "https://raw.githubusercontent.com/moby/moby/master/layer/layer.go",
                "key_structs": ["Layer", "layerStore"],
                "key_funcs": [],
            },
        ],
    },
    "network": {
        "description": "网络管理",
        "files": [
            {
                "path": "api/types/network/network.go",
                "url": "https://raw.githubusercontent.com/moby/moby/master/api/types/network/network.go",
                "key_structs": ["NetworkingConfig", "EndpointSettings"],
                "key_funcs": [],
            },
        ],
    },
    "volume": {
        "description": "存储卷",
        "files": [
            {
                "path": "volume/store.go",
                "url": "https://raw.githubusercontent.com/moby/moby/master/volume/store.go",
                "key_structs": ["Store"],
                "key_funcs": [],
            },
        ],
    },
    "dockerfile": {
        "description": "Dockerfile 构建器",
        "files": [
            {
                "path": "builder/dockerfile/builder.go",
                "url": "https://raw.githubusercontent.com/moby/moby/master/builder/dockerfile/builder.go",
                "key_structs": ["Builder"],
                "key_funcs": ["Build"],
            },
        ],
    },
    "registry": {
        "description": "镜像仓库",
        "files": [
            {
                "path": "registry/registry.go",
                "url": "https://raw.githubusercontent.com/moby/moby/master/registry/registry.go",
                "key_structs": ["Service", "Registry"],
                "key_funcs": ["NewService"],
            },
        ],
    },
    "reference": {
        "description": "镜像引用",
        "files": [
            {
                "path": "reference/reference.go",
                "url": "https://raw.githubusercontent.com/moby/moby/master/reference/reference.go",
                "key_structs": ["Named", "Tagged", "Canonical"],
                "key_funcs": ["ParseNamed"],
            },
        ],
    },
    "cgroups": {
        "description": "cgroups 资源控制",
        "files": [
            {
                "path": "pkg/cgroups/cgroups.go",
                "url": "https://raw.githubusercontent.com/moby/moby/master/pkg/cgroups/cgroups.go",
                "key_structs": ["Cgroup"],
                "key_funcs": [],
            },
        ],
    },
    "namespaces": {
        "description": "Linux namespaces 隔离",
        "files": [
            {
                "path": "pkg/namespaces/namespaces.go",
                "url": "https://raw.githubusercontent.com/moby/moby/master/pkg/namespaces/namespaces.go",
                "key_structs": ["Namespace"],
                "key_funcs": [],
            },
        ],
    },
    "unionfs": {
        "description": "UnionFS 联合文件系统",
        "files": [
            {
                "path": "pkg/unionfs/unionfs.go",
                "url": "https://raw.githubusercontent.com/moby/moby/master/pkg/unionfs/unionfs.go",
                "key_structs": ["UnionFS"],
                "key_funcs": [],
            },
        ],
    },
}


# ============================================================
# Go 源码解析器（基于正则的轻量 AST）
# ============================================================

class GoASTParser:
    """
    轻量级 Go 源码解析器，不依赖 Go 编译器。
    通过正则表达式提取结构体、接口、函数、方法。
    """

    # 正则模式
    STRUCT_PATTERN = re.compile(
        r'(?:^|\n)\s*type\s+(\w+)\s+struct\s*\{([^}]*)\}',
        re.DOTALL,
    )
    INTERFACE_PATTERN = re.compile(
        r'(?:^|\n)\s*type\s+(\w+)\s+interface\s*\{([^}]*)\}',
        re.DOTALL,
    )
    FUNC_PATTERN = re.compile(
        r'(?:^|\n)\s*func\s+(?:\([^)]*\)\s*)?(\w+)\s*\(([^)]*)\)\s*([^{]*)\{',
        re.DOTALL,
    )
    METHOD_PATTERN = re.compile(
        r'(?:^|\n)\s*func\s+\((\w+)\s+\*?(\w+)\)\s+(\w+)\s*\(([^)]*)\)\s*([^{]*)\{',
        re.DOTALL,
    )
    IMPORT_PATTERN = re.compile(
        r'(?:^|\n)\s*import\s*(?:\(\s*([^)]+)\s*\)|"([^"]+)")',
        re.DOTALL,
    )
    CONST_PATTERN = re.compile(
        r'(?:^|\n)\s*const\s*(?:\(\s*([^)]+)\s*\)|(\w+)\s*=\s*([^=\n]+))',
        re.DOTALL,
    )

    @staticmethod
    def parse_source(source_code: str) -> dict:
        """解析 Go 源码，返回结构化数据"""
        result = {
            "structs": [],
            "interfaces": [],
            "functions": [],
            "methods": [],
            "imports": [],
            "constants": [],
        }

        # 提取结构体
        for match in GoASTParser.STRUCT_PATTERN.finditer(source_code):
            name, body = match.group(1), match.group(2)
            fields = GoASTParser._parse_struct_fields(body)
            result["structs"].append({
                "name": name,
                "fields": fields,
                "raw_body": body.strip()[:500],
            })

        # 提取接口
        for match in GoASTParser.INTERFACE_PATTERN.finditer(source_code):
            name, body = match.group(1), match.group(2)
            methods = GoASTParser._parse_interface_methods(body)
            result["interfaces"].append({
                "name": name,
                "methods": methods,
                "raw_body": body.strip()[:500],
            })

        # 提取函数
        for match in GoASTParser.FUNC_PATTERN.finditer(source_code):
            name, params, returns = match.group(1), match.group(2), match.group(3)
            result["functions"].append({
                "name": name,
                "params": params.strip(),
                "returns": returns.strip(),
            })

        # 提取方法
        for match in GoASTParser.METHOD_PATTERN.finditer(source_code):
            receiver, type_name, method, params, returns = (
                match.group(1), match.group(2), match.group(3),
                match.group(4), match.group(5),
            )
            result["methods"].append({
                "receiver": receiver,
                "type": type_name,
                "name": method,
                "params": params.strip(),
                "returns": returns.strip(),
            })

        # 提取 import
        for match in GoASTParser.IMPORT_PATTERN.finditer(source_code):
            imports = match.group(1) or match.group(2)
            if imports:
                for imp in imports.split("\n"):
                    imp = imp.strip().strip('"')
                    if imp and not imp.startswith("//"):
                        result["imports"].append(imp)

        return result

    @staticmethod
    def _parse_struct_fields(body: str) -> list:
        """解析结构体字段"""
        fields = []
        for line in body.split("\n"):
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            # 跳过嵌套结构体
            if "struct" in line or "interface" in line:
                continue
            # 字段格式: Name Type `tags`
            parts = line.split("`")[0].strip().split()
            if len(parts) >= 2:
                fields.append({"name": parts[0], "type": " ".join(parts[1:])})
            elif len(parts) == 1 and parts[0]:
                # 嵌入类型
                fields.append({"name": parts[0], "type": "embedded"})
        return fields

    @staticmethod
    def _parse_interface_methods(body: str) -> list:
        """解析接口方法签名"""
        methods = []
        for line in body.split("\n"):
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            if "(" in line:
                methods.append(line)
        return methods


# ============================================================
# Docker 源码获取器
# ============================================================

class DockerSourceFetcher:
    """从 GitHub 获取 Docker 源码文件"""

    CACHE_DIR = Path(".cache/docker-source")

    @staticmethod
    def fetch_file(url: str, use_cache: bool = True) -> Optional[str]:
        """获取源码文件内容"""
        cache_path = DockerSourceFetcher.CACHE_DIR / url.replace("/", "_").replace(":", "_")

        # 检查缓存
        if use_cache and cache_path.exists():
            try:
                return cache_path.read_text(encoding="utf-8")
            except Exception:
                pass

        # 从网络获取
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "docker-learn-system/1.0")
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode("utf-8", errors="replace")

            # 缓存
            DockerSourceFetcher.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(content, encoding="utf-8")
            return content
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            return None

    @staticmethod
    def fetch_category(category: str) -> dict:
        """获取某个分类下的所有源码"""
        if category not in DOCKER_SOURCE_FILES:
            return {}

        result = {}
        for file_info in DOCKER_SOURCE_FILES[category]["files"]:
            content = DockerSourceFetcher.fetch_file(file_info["url"])
            if content:
                result[file_info["path"]] = {
                    "content": content,
                    "key_structs": file_info.get("key_structs", []),
                    "key_funcs": file_info.get("key_funcs", []),
                }
        return result


# ============================================================
# 源码分析引擎
# ============================================================

class SourceAnalyzer:
    """
    分析 Docker 源码，提取关键信息并与知识图谱关联。
    """

    def __init__(self):
        self.parser = GoASTParser()
        self.fetcher = DockerSourceFetcher()
        self._analysis_cache = {}

    def analyze_concept(self, concept_name: str) -> dict:
        """分析某个概念相关的源码"""
        if concept_name in self._analysis_cache:
            return self._analysis_cache[concept_name]

        # 找到对应的分类
        category = self._find_category(concept_name)
        if not category:
            return {"error": f"没有找到 {concept_name} 对应的源码分类"}

        # 获取源码
        source_files = self.fetcher.fetch_category(category)
        if not source_files:
            return {"error": "无法获取源码文件（可能需要网络连接）"}

        # 解析每个文件
        analysis = {
            "concept": concept_name,
            "category": category,
            "category_description": DOCKER_SOURCE_FILES[category]["description"],
            "files": {},
            "summary": {
                "total_structs": 0,
                "total_interfaces": 0,
                "total_functions": 0,
                "total_methods": 0,
                "key_types": [],
            },
        }

        for path, file_info in source_files.items():
            parsed = self.parser.parse_source(file_info["content"])
            analysis["files"][path] = {
                "parsed": parsed,
                "key_structs": file_info["key_structs"],
                "key_funcs": file_info["key_funcs"],
                "size_kb": len(file_info["content"]) // 1024,
            }
            analysis["summary"]["total_structs"] += len(parsed["structs"])
            analysis["summary"]["total_interfaces"] += len(parsed["interfaces"])
            analysis["summary"]["total_functions"] += len(parsed["functions"])
            analysis["summary"]["total_methods"] += len(parsed["methods"])

            # 提取关键类型
            for struct in parsed["structs"]:
                if struct["name"] in file_info["key_structs"]:
                    analysis["summary"]["key_types"].append({
                        "kind": "struct",
                        "name": struct["name"],
                        "file": path,
                        "fields": struct["fields"][:8],  # 限制字段数
                    })

        self._analysis_cache[concept_name] = analysis
        return analysis

    def generate_source_report(self, concept_name: str) -> str:
        """生成源码分析报告"""
        analysis = self.analyze_concept(concept_name)

        if "error" in analysis:
            return f"⚠️ {analysis['error']}"

        lines = [
            f"# 🔍 源码分析报告: {concept_name}",
            f"",
            f"*分类: {analysis['category_description']}*",
            f"",
            f"---",
            f"",
            f"## 📊 概览",
            f"",
            f"| 指标 | 数量 |",
            f"|------|------|",
            f"| 源码文件 | {len(analysis['files'])} |",
            f"| 结构体 | {analysis['summary']['total_structs']} |",
            f"| 接口 | {analysis['summary']['total_interfaces']} |",
            f"| 函数 | {analysis['summary']['total_functions']} |",
            f"| 方法 | {analysis['summary']['total_methods']} |",
            f"",
        ]

        # 关键类型详情
        if analysis["summary"]["key_types"]:
            lines.append("## 🔑 关键类型")
            lines.append("")
            for kt in analysis["summary"]["key_types"]:
                lines.append(f"### `{kt['name']}` ({kt['kind']})")
                lines.append("")
                lines.append(f"**文件**: `{kt['file']}`")
                lines.append("")
                if kt["fields"]:
                    lines.append("| 字段 | 类型 |")
                    lines.append("|------|------|")
                    for field in kt["fields"]:
                        lines.append(f"| `{field['name']}` | `{field['type']}` |")
                    lines.append("")

        # 每个文件的分析
        lines.append("## 📁 文件详情")
        lines.append("")
        for path, file_analysis in analysis["files"].items():
            parsed = file_analysis["parsed"]
            lines.append(f"### `{path}` ({file_analysis['size_kb']} KB)")
            lines.append("")

            if parsed["structs"]:
                lines.append(f"**结构体** ({len(parsed['structs'])}):")
                for s in parsed["structs"][:10]:
                    field_names = ", ".join(f["name"] for f in s["fields"][:5])
                    if len(s["fields"]) > 5:
                        field_names += "..."
                    lines.append(f"- `{s['name']}`: {field_names}")
                if len(parsed["structs"]) > 10:
                    lines.append(f"- ... 还有 {len(parsed['structs']) - 10} 个")
                lines.append("")

            if parsed["interfaces"]:
                lines.append(f"**接口** ({len(parsed['interfaces'])}):")
                for iface in parsed["interfaces"][:10]:
                    method_count = len(iface["methods"])
                    lines.append(f"- `{iface['name']}` ({method_count} 方法)")
                lines.append("")

            if parsed["functions"]:
                lines.append(f"**函数** ({len(parsed['functions'])}):")
                for func in parsed["functions"][:10]:
                    ret = func["returns"][:40] if func["returns"] else "void"
                    lines.append(f"- `{func['name']}({func['params'][:40]})` → {ret}")
                if len(parsed["functions"]) > 10:
                    lines.append(f"- ... 还有 {len(parsed['functions']) - 10} 个")
                lines.append("")

            if parsed["methods"]:
                lines.append(f"**方法** ({len(parsed['methods'])}):")
                for method in parsed["methods"][:10]:
                    lines.append(
                        f"- `({method['receiver']} {method['type']}) {method['name']}()`"
                    )
                if len(parsed["methods"]) > 10:
                    lines.append(f"- ... 还有 {len(parsed['methods']) - 10} 个")
                lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*注: 此报告由 Go AST 解析引擎基于 Docker 源码生成。*")
        lines.append("*完整源码: https://github.com/moby/moby*")

        return "\n".join(lines)

    def _find_category(self, concept_name: str) -> Optional[str]:
        """根据概念名找到对应的源码分类"""
        # 中文名映射
        category_map = {
            "容器": "container",
            "container": "container",
            "镜像": "image",
            "image": "image",
            "层": "layer",
            "layer": "layer",
            "容器运行时": "runtime",
            "runtime": "runtime",
            "container runtime": "runtime",
            "dockerd": "daemon",
            "daemon": "daemon",
            "守护进程": "daemon",
            "网络": "network",
            "network": "network",
            "卷": "volume",
            "volume": "volume",
            "存储卷": "volume",
            "客户端": "client",
            "client": "client",
            "构建": "dockerfile",
            "dockerfile": "dockerfile",
            "仓库": "registry",
            "registry": "registry",
            "cgroups": "cgroups",
            "namespaces": "namespaces",
            "namespace": "namespaces",
            "unionfs": "unionfs",
            "api": "api_types",
            "api types": "api_types",
        }

        for key, cat in category_map.items():
            if key.lower() in concept_name.lower():
                return cat
        return None

    def get_cache_status(self) -> dict:
        """获取缓存状态"""
        cache_dir = DockerSourceFetcher.CACHE_DIR
        if cache_dir.exists():
            files = list(cache_dir.iterdir())
            return {
                "cached_files": len(files),
                "total_size_kb": sum(f.stat().st_size for f in files) // 1024,
            }
        return {"cached_files": 0, "total_size_kb": 0}


# ============================================================
# 全局实例
# ============================================================

source_analyzer = SourceAnalyzer()
