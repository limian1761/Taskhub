#!/usr/bin/env python3
"""
Outline客户端测试脚本
用于验证新的Outline API客户端功能
"""

import asyncio
import sys
import os

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from taskhub.sdk.outline_client import OutlineClient

async def test_outline_client():
    """测试Outline客户端各项功能"""\    try:
        print("🧪 开始测试Outline客户端...")
        
        # 创建客户端实例
        client = OutlineClient()
        
        print(f"🔗 连接到: {client.base_url}")
        
        # 测试获取当前用户信息
        try:
            user_info = await client.get_current_user()
            print(f"✅ 用户验证成功: {user_info.get('data', {}).get('name', 'Unknown')}")
        except Exception as e:
            print(f"❌ 用户验证失败: {e}")
            return False
        
        # 测试列出集合
        try:
            collections = await client.list_collections(limit=5)
            print(f"✅ 集合查询成功: 找到 {len(collections.get('data', []))} 个集合")
            
            for collection in collections.get('data', [])[:3]:
                print(f"   📁 {collection.get('name')} (ID: {collection.get('id')})")
                
        except Exception as e:
            print(f"❌ 集合查询失败: {e}")
        
        # 如果存在集合，测试创建文档
        collections = await client.list_collections(limit=1)
        if collections.get('data'):
            collection_id = collections['data'][0]['id']
            
            # 创建测试文档
            try:
                test_doc = await client.create_document(
                    title="测试文档 - Outline客户端验证",
                    content="""# 测试文档

这是使用新的Outline客户端创建的测试文档。

## 功能验证
- ✅ 客户端连接
- ✅ 文档创建
- ✅ 集合操作

## 测试内容
该文档用于验证Outline API客户端的所有基本功能是否正常工作。
""",
                    collection_id=collection_id,
                    publish=True
                )
                
                doc_id = test_doc.get('data', {}).get('id')
                print(f"✅ 文档创建成功: ID={doc_id}")
                
                # 测试获取文档
                retrieved_doc = await client.get_document(doc_id)
                print(f"✅ 文档检索成功: {retrieved_doc.get('data', {}).get('title')}")
                
                # 测试更新文档
                updated_doc = await client.update_document(
                    document_id=doc_id,
                    text="""# 更新后的测试文档

该文档已被更新，验证更新功能正常。

## 更新内容
- 文档内容已修改
- 验证更新API调用
- 测试文档生命周期管理
"""
                )
                print(f"✅ 文档更新成功")
                
                # 清理：删除测试文档
                deleted = await client.delete_document(doc_id)
                print(f"✅ 文档清理完成: {'已删除' if deleted else '删除失败'}")
                
            except Exception as e:
                print(f"❌ 文档操作失败: {e}")
        
        # 测试搜索功能
        try:
            search_results = await client.search_documents("测试", limit=5)
            print(f"✅ 搜索功能正常: 找到 {len(search_results.get('data', []))} 个结果")
        except Exception as e:
            print(f"❌ 搜索功能失败: {e}")
        
        print("\n🎉 所有测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

async def main():
    """主测试函数"""\    success = await test_outline_client()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)