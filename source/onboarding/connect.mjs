import { existsSync, readFileSync, writeFileSync, mkdirSync, renameSync } from 'node:fs';
import { dirname, resolve, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { createInterface } from 'node:readline/promises';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const command = resolve(root, 'runtime/x64/node.exe');
const entry = resolve(root, 'app/bin/chan-kg-mcp.mjs');
const cli = resolve(root, 'app/bin/chan-kg.mjs');
const server = { command, args: [entry] };
const mode = process.argv[2] || 'generate';
const output = resolve(root, '连接资料');
const json = value => JSON.stringify(value, null, 2) + '\n';

async function main() {
  for (const file of [command, entry, cli]) if (!existsSync(file)) throw new Error('文件不完整。请先把整个压缩包解压，再从解压后的文件夹运行。缺少：' + file);
  if (mode === 'check') {
    console.log('正在检查文件并试查“中枢”的原文。首次加载可能需要几分钟，请等待。');
    const report = { started_at: new Date().toISOString(), passed: false, root, steps: [] };
    const call = args => {
      const result = spawnSync(command, [cli, ...args], { encoding: 'utf8', cwd: root, windowsHide: true,
        timeout: 300000, maxBuffer: 16 * 1024 * 1024 });
      if (result.status !== 0) throw new Error(result.error?.message || result.stderr || '运行失败');
      return JSON.parse(result.stdout);
    };
    const status = call(['status']);
    if (status.data.index_problem || status.data.dense_problem || !status.data.capabilities.dense || !status.data.capabilities.rerank) throw new Error('知识文件、模型或索引未就绪。');
    report.steps.push('knowledge_models_indexes_ready');
    console.log('1/2 通过：知识文件、模型和检索索引已就绪。');
    const result = call(['retrieve', '中枢是什么，成立需要什么条件？', '--limit', '5']);
    if (result.runtime.degraded || !result.data.reviewed.some(x => x.id === 'upper-l017-center-definition')) throw new Error('检索未返回预期的中枢定义。');
    report.steps.push('definition_retrieved_without_degradation'); report.passed = true;
    mkdirSync(output, { recursive: true });
    writeFileSync(resolve(output, '本机检查结果.json'), json(report));
    console.log('2/2 通过：已找到中枢定义，检索没有降级。\n检查通过。现在可按《开始使用.md》连接你的 AI 客户端。\n这个检查证明本地检索能运行；客户端是否连接成功，还要按教程发送测试问题。');
    return;
  }
  if (mode === 'merge') {
    const input = createInterface({ input: process.stdin, output: process.stdout });
    let target;
    try { target = (await input.question('请把客户端配置文件拖入此窗口，然后按回车：\n')).trim().replace(/^"(.*)"$/, '$1'); }
    finally { input.close(); }
    target = resolve(target);
    if (!['claude_desktop_config.json', 'mcp.json'].includes(basename(target).toLowerCase())) throw new Error('请选择 claude_desktop_config.json 或 mcp.json，原文件未改动。');
    if (!existsSync(target)) throw new Error('找不到这个文件，原文件未改动。');
    const original = readFileSync(target, 'utf8');
    let config;
    try { config = JSON.parse(original.replace(/^\uFEFF/, '')); } catch { throw new Error('配置内容不是完整的 JSON，原文件未改动。请先撤销尚未保存的修改，再重试。'); }
    if (!config || Array.isArray(config) || typeof config !== 'object' || (config.mcpServers && (Array.isArray(config.mcpServers) || typeof config.mcpServers !== 'object'))) throw new Error('配置结构无法识别，原文件未改动。');
    if (Object.hasOwn(config.mcpServers || {}, 'chanlun-rag')) throw new Error('已有名为 chanlun-rag 的连接。为避免覆盖，原文件未改动；请先在客户端检查该连接。');
    const backup = target + '.before-chanlun-' + Date.now() + '.bak';
    writeFileSync(backup, original, { flag: 'wx' });
    config.mcpServers = { ...(config.mcpServers || {}), 'chanlun-rag': server };
    const temporary = target + '.chanlun-' + Date.now() + '.tmp';
    writeFileSync(temporary, json(config), { flag: 'wx' });
    renameSync(temporary, target);
    console.log('已加入 chanlun-rag，其他连接已保留。\n备份：' + backup + '\n请完全退出客户端，再重新打开。');
    return;
  }
  if (mode !== 'generate') throw new Error('未知操作。');
  mkdirSync(output, { recursive: true });
  writeFileSync(resolve(output, '客户端配置.json'), json({ mcpServers: { 'chanlun-rag': server } }));
  writeFileSync(resolve(output, 'Codex配置.toml'), '[mcp_servers.chanlun-rag]\ncommand = ' + JSON.stringify(command) + '\nargs = [' + JSON.stringify(entry) + ']\n');
  writeFileSync(resolve(output, '连接说明.txt'), '\uFEFF' + [
    '缠论RAG：本机连接信息', '', '这些信息只适用于当前解压位置。移动文件夹后，请重新运行“开始连接.cmd”并更新客户端。', '',
    '连接名称：chanlun-rag', '类型：STDIO（本地程序）', '', '命令 / Command（复制下一整行，不加引号）：', command, '',
    '参数 / Arguments（只有一项；复制下一整行，不加引号）：', entry, '',
    '工作目录、环境变量：留空。无需另填网址、密钥。', '',
    'Codex：按教程逐项填写上面的命令与参数。',
    'Claude Desktop / WorkBuddy：按教程打开配置。空白配置可复制同目录“客户端配置.json”的全部文字。',
    '已有其他连接：不要覆盖，运行“合并已有配置.cmd”；它会先备份，再加入本项目。', '',
    '完整步骤见解压目录中的“开始使用.md”。'
  ].join('\r\n'));
  console.log('连接信息已生成：\n' + output + '\n\n请打开其中的“连接说明.txt”，再按《开始使用.md》选择客户端。\n这些文件不含账号密码，也不会自动修改任何客户端。');
}
try { await main(); } catch (error) { console.error('\n未完成：' + error.message + '\n请查看《开始使用.md》中的常见问题。'); process.exitCode = 1; }
