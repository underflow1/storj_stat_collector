-- phpMyAdmin SQL Dump
-- version 4.8.5
-- https://www.phpmyadmin.net/
--
-- Хост: localhost
-- Время создания: Дек 03 2019 г., 22:52
-- Версия сервера: 8.0.13-4
-- Версия PHP: 7.2.24-0ubuntu0.18.04.1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- База данных: `zkomw3Ecik`
--

-- --------------------------------------------------------

--
-- Структура таблицы `bandwidth`
--

CREATE TABLE `bandwidth` (
  `id` int(11) NOT NULL,
  `nodeId` varchar(64) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `nodeName` varchar(32) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `date` date NOT NULL,
  `month` tinyint(4) NOT NULL,
  `satelliteId` varchar(64) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `satelliteName` varchar(32) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `action` tinyint(1) NOT NULL,
  `actionName` varchar(16) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `amount` bigint(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `statistics`
--

CREATE TABLE `statistics` (
  `nodeId` varchar(64) CHARACTER SET utf8 COLLATE utf8_unicode_ci DEFAULT NULL,
  `nodeName` varchar(32) COLLATE utf8_unicode_ci NOT NULL,
  `nodeApiData` json NOT NULL,
  `lastDate` date DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Индексы сохранённых таблиц
--

--
-- Индексы таблицы `bandwidth`
--
ALTER TABLE `bandwidth`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `test` (`nodeId`,`date`,`satelliteId`,`action`);

--
-- Индексы таблицы `statistics`
--
ALTER TABLE `statistics`
  ADD UNIQUE KEY `nodeId` (`nodeId`);

--
-- AUTO_INCREMENT для сохранённых таблиц
--

--
-- AUTO_INCREMENT для таблицы `bandwidth`
--
ALTER TABLE `bandwidth`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
