# Gerenciador de Clipes para Blogueiros (Blogger Clip Manager)

This web application helps content creators, particularly video bloggers, manage and process video clips for various social media platforms. It runs entirely in the user's browser, utilizing technologies like FFmpeg.wasm for video processing. All user data, including settings, project information, and generated clip metadata, is stored locally in the browser's `localStorage`.

## File Structure

The project consists of the following main files:

-   `index.html`: The main HTML file that defines the structure and layout of the web application.
-   `style.css`: Contains all the CSS styles used to define the visual appearance of the application.
-   `script.js`: Contains all the JavaScript logic that powers the application's interactive features, video processing, data management, and UI updates.

## Features

-   **Local Video Processing:** Cut and reformat video clips directly in your browser.
-   **YouTube Metadata Fetching:** Retrieve video titles, descriptions, and chapters (if available and API key provided).
-   **Segment Management:** Define and queue multiple segments from a source video for batch processing.
-   **Format Presets:** Easily format clips for different platforms (9:16, 1:1, 16:9).
-   **Configuration:**
    -   Set YouTube API Key.
    -   Define default clip duration.
    -   Choose preferred output format.
    -   Toggle fade effects and audio removal.
-   **Clip Metadata Storage:** Save information about generated clips, including platforms posted to, links, and basic performance metrics (views, likes, comments).
-   **Metrics Analysis:** Basic dashboard to view saved clip metrics and simple insights.
-   **User Notes:** A section to keep personal notes on content performance.
-   **Data Management (Export/Import):**
    -   Allows users to backup all their application data (settings, clip information, metrics, notes).
    -   Enables restoration of data from a backup file, useful for migrating between browsers or recovering from data loss.

## Usage

1.  Open `index.html` in a modern web browser (Chrome, Firefox, Edge recommended).
2.  **Initial Setup (Optional but Recommended):**
    *   Navigate to the "Configurações" (Settings) section.
    *   Enter your YouTube Data API v3 Key if you wish to fetch video metadata directly from YouTube.
    *   Adjust default clip duration, output format, and other preferences.
3.  **Video Processing:**
    *   Go to the "Processamento de Vídeo" (Video Processing) section.
    *   If using YouTube metadata, paste the YouTube video URL and click "Buscar Metadados".
    *   Upload your local video file using the "Upload do Arquivo de Vídeo Local" input.
    *   Click "Carregar FFmpeg" (this may take a moment on first use as it downloads the necessary FFmpeg core files).
    *   Define segments for cutting by specifying start/end times and a title, then add them to the queue.
    *   Once all desired segments are in the queue, click "Iniciar Processamento dos Clipes na Fila".
4.  **Generated Clips:**
    *   Navigate to the "Clipes Gerados" (Generated Clips) section.
    *   Here you can preview generated clips, download them, and log where you've posted them along with performance metrics.
5.  **Metrics Analysis:**
    *   Visit the "Análise de Métricas" (Metrics Analysis) section to see a summary of your saved clip data and any insights generated.
6.  **Data Management (Export/Import):**
    *   These options are available in the "Configurações" (Settings) section under "Gerenciamento de Dados".
    *   **Exporting Data:**
        *   Click the "Exportar Todos os Dados" button.
        *   A file named `blogger-studio-backup.json` will be generated and downloaded by your browser.
        *   **Important:** Save this file in a safe place. It's recommended to export your data regularly as a backup measure, especially if you clear browser data or switch browsers.
    *   **Importing Data:**
        *   Click the "Escolher arquivo" (Choose file) button next to "Importar Dados de Backup".
        *   Select a previously exported `blogger-studio-backup.json` file from your computer.
        *   Click the "Importar Dados" button.
        *   **Caution:** Importing data will overwrite any existing settings, clip information, and notes currently in the application with the content from the backup file. The application will then refresh its state to reflect the imported data.

**Important Considerations:**

*   **Browser-Based:** All operations and data storage are local to your browser. Clearing your browser's cache or site data will erase all your saved information unless you have an exported backup.
*   **Performance:** Video processing can be resource-intensive. Performance depends on your computer's hardware and the size/length of the videos being processed.
*   **YouTube Terms of Service:** The tool does not download videos from YouTube. Users must provide their own video files.

This README provides a basic guide. Explore the different sections of the application to discover all its capabilities.