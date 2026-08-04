<script setup></script>

<template>
  <footer class="app-footer">
    <div class="container footer-inner">
      <div class="footer-main">
        <div class="brand">
          <div class="logo">
            <span class="logo-text">SimpleMall</span>
          </div>
          <p class="tagline">精选品质好物，打造简单购物体验</p>
        </div>
        <div class="links">
          <div class="link-group">
            <h4>购物指南</h4>
            <a href="#">购物流程</a>
            <a href="#">会员介绍</a>
            <a href="#">常见问题</a>
          </div>
          <div class="link-group">
            <h4>售后服务</h4>
            <a href="#">退换货政策</a>
            <a href="#">价格保护</a>
            <a href="#">投诉建议</a>
          </div>
          <div class="link-group">
            <h4>关于我们</h4>
            <a href="#">品牌故事</a>
            <a href="#">联系我们</a>
            <a href="#">加入我们</a>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <p>© 2026 SimpleMall. All rights reserved.</p>
        <div class="badges">
          <span>企业级电商教学系统</span>
          <span>|</span>
          <span>Django + Vue3</span>
        </div>
      </div>
    </div>
  </footer>
</template>

<style scoped lang="scss">
.app-footer {
  background: $color-apple-gray;
  color: $text-secondary;
  margin-top: auto;
  border-top: 1px solid $border-color;
}

.footer-inner {
  padding: $space-12 $container-padding $space-6;
}

.footer-main {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: $space-12;
  padding-bottom: $space-10;
  border-bottom: 1px solid $border-color;
}

.brand {
  .logo {
    display: flex;
    align-items: center;
    gap: $space-3;
    margin-bottom: $space-4;

    .logo-text {
      font-family: $font-display;
      font-size: 22px;
      font-weight: 700;
      color: $text-primary;
      letter-spacing: -0.04em;
    }
  }

  .tagline {
    font-size: 14px;
    line-height: 1.7;
    color: $text-secondary;
  }
}

.links {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $space-8;
}

.link-group {
  h4 {
    color: $text-primary;
    font-size: 13px;
    font-weight: 700;
    margin-bottom: $space-4;
    letter-spacing: -0.01em;
  }

  a {
    display: block;
    font-size: 13px;
    color: $text-secondary;
    margin-bottom: $space-3;
    transition: color $transition-fast;

    &:hover {
      color: $text-primary;
      text-decoration: underline;
    }
  }
}

.footer-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: $space-6;
  font-size: 12px;
  color: $text-secondary;

  .badges {
    display: flex;
    align-items: center;
    gap: $space-3;
  }
}

@media (max-width: 768px) {
  .footer-main {
    grid-template-columns: 1fr;
    gap: $space-8;
  }

  .links {
    grid-template-columns: repeat(2, 1fr);
  }

  .footer-bottom {
    flex-direction: column;
    gap: $space-3;
    text-align: center;
  }
}
</style>
