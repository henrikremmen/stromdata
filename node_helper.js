const NodeHelper = require("node_helper");
const { spawn } = require("node:child_process");
const path = require("node:path");

module.exports = NodeHelper.create({
  start() {
    this.config = null;
    this.timer = null;
    this.running = false;
  },

  stop() {
    if (this.timer) {
      clearTimeout(this.timer);
    }
  },

  socketNotificationReceived(notification, payload) {
    if (notification !== "STROMDATA_CONFIG") {
      return;
    }

    this.config = payload;
    this.generatePlot();
    this.scheduleNextRun();
  },

  scheduleNextRun() {
    if (this.timer) {
      clearTimeout(this.timer);
    }

    const now = new Date();
    const next = new Date(now);
    next.setHours(now.getHours() + 1, this.config.updateAtMinute, 0, 0);

    this.timer = setTimeout(() => {
      this.generatePlot();
      this.scheduleNextRun();
    }, next.getTime() - now.getTime());
  },

  generatePlot() {
    if (this.running) {
      return;
    }
    this.running = true;

    const pythonPath = path.resolve(this.path, this.config.pythonPath);
    const scriptPath = path.join(this.path, "plots.py");
    const outputPath = path.join(this.path, "public", "stromdata.png");
    const process = spawn(
      pythonPath,
      [scriptPath, "--output", outputPath],
      {
        cwd: this.path,
        env: { ...global.process.env, MPLBACKEND: "Agg" },
      },
    );

    let errorOutput = "";
    process.stderr.on("data", (data) => {
      errorOutput += data.toString();
    });

    process.on("error", (error) => {
      this.running = false;
      this.sendSocketNotification("STROMDATA_ERROR", {
        message: error.message,
      });
    });

    process.on("close", (code) => {
      this.running = false;
      if (code === 0) {
        this.sendSocketNotification("STROMDATA_UPDATED", {
          updatedAt: Date.now(),
        });
        return;
      }

      const message = errorOutput.trim() || `Python avsluttet med kode ${code}`;
      console.error(`[MMM-Stromdata] ${message}`);
      this.sendSocketNotification("STROMDATA_ERROR", { message });
    });
  },
});
