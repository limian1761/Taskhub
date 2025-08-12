# Outline API 知识库文档

## 概述
Outline API 是一个RPC风格的API，允许开发者程序化地与Outline知识库的所有数据进行交互。官方应用本身就是构建在相同的API之上。

## API结构
- **风格**: RPC (Remote Procedure Call)
- **协议**: HTTPS only
- **数据格式**: JSON
- **规范**: 提供OpenAPI规范文档，可用于生成各种编程语言的客户端

## 认证方式

### 1. API Key认证（推荐）
- **获取方式**: 在Outline设置中 Settings => API & Apps 创建
- **使用方式**: HTTP请求头中添加 `Authorization: Bearer YOUR_API_KEY`
- **注意事项**: 
  - API密钥提供对所有文档的访问权限
  - 应像密码一样妥善保管
  - 不应提交到源代码控制

### 2. OAuth 2.0认证
- **适用场景**: 第三方应用集成
- **流程**:
  1. 在 Settings => Applications 注册应用
  2. 交换客户端凭据获取访问令牌
  3. 使用访问令牌进行API请求

## 请求格式

### 基本结构
```
POST https://app.getoutline.com/api/:method
```

### 请求头
```
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
Accept: application/json
```

### 示例请求（curl）
```bash
curl https://app.getoutline.com/api/documents.info \
  -X 'POST' \
  -H 'authorization: Bearer MY_API_KEY' \
  -H 'content-type: application/json' \
  -H 'accept: application/json' \
  -d '{"id": "outline-api-NTpezNwhUP"}'
```

### 示例请求（JavaScript）
```javascript
const response = await fetch("https://app.getoutline.com/api/documents.info", {
  method: "POST",
  headers: {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Bearer MY_API_KEY"
  },
  body: JSON.stringify({
    id: "outline-api-NTpezNwhUP"
  })
});

const body = await response.json();
const document = body.data;
```

## 权限范围（Scopes）

### 文档相关
- `documents.read`: 读取文档
- `documents.write`: 写入文档
- `documents.*`: 所有文档操作

### 用户相关
- `users.*`: 所有用户相关操作

### 通用范围
- `read`: 所有读取操作
- `write`: 所有写入操作

## 响应格式

### 成功响应
```json
{
  "ok": true,
  "status": 200,
  "data": {...}
}
```

### 分页响应
```json
{
  "ok": true,
  "status": 200,
  "data": [...],
  "pagination": {
    "limit": 25,
    "offset": 0,
    "nextPath": "/api/documents.list?limit=25&offset=25"
  }
}
```

### 错误响应
```json
{
  "ok": false,
  "error": "Not Found"
}
```

## 主要资源端点

### 文档（Documents）
- **documents.list**: 获取文档列表
- **documents.info**: 获取文档详情
- **documents.create**: 创建文档
- **documents.update**: 更新文档
- **documents.delete**: 删除文档

### 集合（Collections）
- **collections.list**: 获取集合列表
- **collections.info**: 获取集合详情
- **collections.create**: 创建集合
- **collections.update**: 更新集合
- **collections.delete**: 删除集合

### 搜索
- **documents.search**: 搜索文档
- **collections.search**: 搜索集合

## 错误处理
- **成功状态码**: 200, 201
- **错误状态码**: 根据错误类型返回相应HTTP状态码
- **错误格式**: 统一包含 `ok: false` 和错误消息

## 速率限制
- **限制策略**: 变更数据的端点比只读端点更严格
- **超出限制**: 返回429 Too Many Requests状态码
- **重试机制**: 响应包含 `Retry-After` 头，指示等待秒数

## 策略（Policies）
- **作用**: 描述当前认证对特定资源的授权操作
- **结构**: 策略ID与相关资源相同
- **使用场景**: 可用于界面中调整可见元素

## 最佳实践

### 1. 认证安全
- 使用环境变量存储API密钥
- 定期轮换API密钥
- 限制API密钥权限范围

### 2. 错误处理
- 检查响应的 `ok` 字段
- 实施重试机制处理429错误
- 记录错误日志用于调试

### 3. 性能优化
- 使用分页参数避免大列表查询
- 缓存常用数据
- 批量操作减少API调用次数

### 4. 版本控制
- 关注API版本更新
- 使用OpenAPI规范生成客户端
- 测试新版本的兼容性

## 开发工具

### OpenAPI规范
- 可用于生成类型安全的客户端
- 支持多种编程语言
- 提供IDE自动补全

### 测试工具
- Postman集合
- curl命令测试
- 自定义测试脚本

## 相关资源
- [官方API文档](https://www.getoutline.com/developers)
- [OpenAPI规范](https://app.getoutline.com/api/openapi.json)
- [GitHub讨论](https://github.com/outline/outline/discussions)