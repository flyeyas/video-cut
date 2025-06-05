#!/bin/bash

# 视频智能镜头分割与组合工具 - Mac OS 应用程序打包脚本

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}  视频智能镜头分割与组合工具 - Mac OS 应用程序打包  ${NC}"
echo -e "${BLUE}====================================================${NC}"
echo 

# 检查Python环境
echo -e "${YELLOW}[1/6] 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python3，请先安装Python 3.6或更高版本。${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}已找到Python版本: ${PYTHON_VERSION}${NC}"

# 安装依赖
echo -e "\n${YELLOW}[2/6] 安装必要的依赖...${NC}"
echo -e "${BLUE}安装py2app...${NC}"
pip3 install py2app

echo -e "${BLUE}安装项目依赖...${NC}"
pip3 install -r requirements_gui.txt

# 检查图标文件
echo -e "\n${YELLOW}[3/6] 检查应用图标...${NC}"
if [ ! -f "app_icon.icns" ]; then
    echo -e "${YELLOW}未找到app_icon.icns文件。${NC}"
    
    if [ -f "app_icon.svg" ]; then
        echo -e "${BLUE}找到SVG图标文件，但需要转换为ICNS格式。${NC}"
        echo -e "${YELLOW}请按照mac_app_build_guide.md中的说明将SVG转换为ICNS格式。${NC}"
        echo -e "${YELLOW}转换完成后，请重新运行此脚本。${NC}"
        
        # 询问用户是否继续
        read -p "是否继续打包过程（将使用默认图标）？(y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo -e "${YELLOW}未找到图标文件，将使用默认图标。${NC}"
    fi
else
    echo -e "${GREEN}已找到ICNS图标文件。${NC}"
fi

# 清理之前的构建
echo -e "\n${YELLOW}[4/6] 清理之前的构建...${NC}"
rm -rf build dist
echo -e "${GREEN}清理完成。${NC}"

# 打包应用程序
echo -e "\n${YELLOW}[5/6] 打包应用程序...${NC}"
echo -e "${BLUE}这个过程可能需要几分钟时间，请耐心等待...${NC}"
python3 setup.py py2app

# 检查打包结果
echo -e "\n${YELLOW}[6/6] 检查打包结果...${NC}"
if [ -d "dist/视频智能镜头分割与组合工具.app" ]; then
    echo -e "${GREEN}应用程序打包成功！${NC}"
    echo -e "${BLUE}应用程序位置: ${PWD}/dist/视频智能镜头分割与组合工具.app${NC}"
    
    # 询问是否打开应用程序
    read -p "是否立即打开应用程序？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "dist/视频智能镜头分割与组合工具.app"
    fi
else
    echo -e "${RED}应用程序打包失败，请检查错误信息。${NC}"
    exit 1
fi

echo -e "\n${GREEN}打包过程完成！${NC}"
echo -e "${BLUE}如需了解更多信息，请查看mac_app_build_guide.md文件。${NC}"