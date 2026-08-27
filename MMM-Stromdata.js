Module.register("MMM-Stromdata", {
  defaults: {
    width: 1000,
    updateAtMinute: 2,
    pythonPath: ".venv/bin/python",
  },

  start() {
    this.imageVersion = 0;
    this.statusMessage = "Henter strømdata …";
    this.sendSocketNotification("STROMDATA_CONFIG", this.config);
  },

  getStyles() {
    return ["MMM-Stromdata.css"];
  },

  getDom() {
    const wrapper = document.createElement("div");
    wrapper.className = "stromdata-wrapper";
    wrapper.style.maxWidth = `${this.config.width}px`;

    if (!this.imageVersion) {
      wrapper.textContent = this.statusMessage;
      wrapper.classList.add("dimmed", "light", "small");
      return wrapper;
    }

    const image = document.createElement("img");
    image.className = "stromdata-plot";
    image.src = `${this.file("public/stromdata.png")}?v=${this.imageVersion}`;
    image.alt = "Spotpris, forbruk og spotkostnad siste syv dager";
    wrapper.appendChild(image);
    return wrapper;
  },

  socketNotificationReceived(notification, payload) {
    if (notification === "STROMDATA_UPDATED") {
      this.imageVersion = payload.updatedAt;
      this.statusMessage = "";
      this.updateDom(500);
    }

    if (notification === "STROMDATA_ERROR") {
      this.statusMessage = `Strømdata-feil: ${payload.message}`;
      this.updateDom(500);
    }
  },
});
